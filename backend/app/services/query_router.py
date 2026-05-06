"""
智能查询路由器（自动选择最佳存储引擎）
"""
import logging
from typing import Any, Optional

from .elasticsearch_client import es_client
from ..extensions import db
from ..utils.cache import cache_strategy

logger = logging.getLogger(__name__)


class QueryRouter:
    """智能查询路由器"""
    
    def execute(self, query_type: str, params: dict) -> dict:
        """
        根据查询类型自动选择存储引擎
        
        路由规则：
        - exact_match → PostgreSQL
        - fulltext_search → Elasticsearch
        - realtime_data → Redis
        - aggregation → Elasticsearch
        - hybrid_search → PG + ES
        """
        
        # 先检查缓存
        cache_key = f"{query_type}:{hash(str(params))}"
        cached = cache_strategy.get_cached('search_results', cache_key)
        if cached:
            return {**cached, 'cached': True}
        
        result = None
        
        if query_type == 'exact_match':
            result = self._query_postgresql(params)
        elif query_type == 'fulltext_search':
            result = self._query_elasticsearch(params)
        elif query_type == 'aggregation':
            result = self._query_elasticsearch_agg(params)
        elif query_type == 'hybrid_search':
            result = self._hybrid_search(params)
        else:
            result = {'error': f'Unknown query_type: {query_type}'}
        
        # 缓存结果
        if result and 'error' not in result:
            cache_strategy.set_cached('search_results', cache_key, result)
        
        return result
    
    def _query_postgresql(self, params: dict) -> dict:
        """PostgreSQL 精确查询"""
        from sqlalchemy import text
        
        table = params.get('table')
        conditions = params.get('conditions', {})
        
        where_clauses = []
        query_params = {}
        
        for key, value in conditions.items():
            where_clauses.append(f"{key} = :{key}")
            query_params[key] = value
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = text(f"""
            SELECT * FROM {table}
            WHERE {where_sql}
            LIMIT :limit
        """)
        
        query_params['limit'] = params.get('limit', 100)
        
        results = db.session.execute(query, query_params).fetchall()
        
        return {
            'source': 'postgresql',
            'total': len(results),
            'results': [dict(row._mapping) for row in results]
        }
    
    def _query_elasticsearch(self, params: dict) -> dict:
        """Elasticsearch 全文检索"""
        
        index = params.get('index', 'news_articles')
        keyword = params.get('keyword', '')
        
        # 构建查询
        es_query = {"bool": {"must": [], "filter": []}}
        
        if keyword:
            es_query['bool']['must'].append({
                "multi_match": {
                    "query": keyword,
                    "fields": ["title^3", "content", "summary^2", "company_name^2"],
                    "type": "best_fields"
                }
            })
        
        # 过滤条件
        if 'symbols' in params:
            es_query['bool']['filter'].append({
                "terms": {"symbols": params['symbols']}
            })
        
        if 'categories' in params:
            es_query['bool']['filter'].append({
                "terms": {"categories": params['categories']}
            })
        
        if 'date_range' in params:
            date_range = params['date_range']
            es_query['bool']['filter'].append({
                "range": {
                    "published_at": {
                        "gte": date_range.get('start'),
                        "lte": date_range.get('end')
                    }
                }
            })
        
        if 'sentiment_range' in params:
            es_query['bool']['filter'].append({
                "range": {
                    "sentiment_score": params['sentiment_range']
                }
            })
        
        # 执行查询
        response = es_client.search(
            index=index,
            query=es_query,
            size=params.get('size', 10),
            from_=params.get('from', 0),
            sort=params.get('sort', [{"published_at": "desc"}])
        )
        
        return {
            'source': 'elasticsearch',
            'total': response['hits']['total']['value'],
            'results': [hit['_source'] for hit in response['hits']['hits']],
            'took_ms': response['took']
        }
    
    def _query_elasticsearch_agg(self, params: dict) -> dict:
        """Elasticsearch 聚合分析"""
        
        index = params.get('index', 'security_companies')
        
        agg_query = {
            "size": 0,
            "aggs": {
                "by_sector": {
                    "terms": {"field": "sector", "size": 20}
                },
                "by_exchange": {
                    "terms": {"field": "exchange", "size": 10}
                }
            }
        }
        
        # 添加自定义聚合
        if 'custom_aggs' in params:
            agg_query['aggs'].update(params['custom_aggs'])
        
        response = es_client.client.search(
            index=index,
            query={"match_all": {}},
            aggs=agg_query['aggs']
        )
        
        return {
            'source': 'elasticsearch',
            'aggregations': response['aggregations']
        }
    
    def _hybrid_search(self, params: dict) -> dict:
        """
        混合搜索（PostgreSQL + Elasticsearch）
        先 ES 全文检索获取 ID 列表，再 PG 获取完整关联数据
        """
        from sqlalchemy import text
        
        # Step 1: ES 检索获取 ID 列表
        es_results = self._query_elasticsearch(params)
        
        # 提取 ID
        table = params.get('table', 'news_articles')
        id_field = params.get('id_field', 'article_id')
        
        record_ids = []
        for result in es_results['results']:
            doc_id = result.get(id_field, result.get('id'))
            if doc_id:
                # 移除表名前缀，只保留数字 ID
                if isinstance(doc_id, str) and '_' in doc_id:
                    doc_id = doc_id.split('_')[-1]
                record_ids.append(int(doc_id))
        
        if not record_ids:
            return {"total": 0, "results": [], "sources": []}
        
        # Step 2: PostgreSQL 获取完整数据
        # 根据表名构建 JOIN 查询
        if table == 'news_articles':
            pg_query = text("""
                SELECT na.*, 
                       sc.company_name,
                       sc.sector
                FROM news_articles na
                LEFT JOIN security_companies sc 
                    ON na.related_symbols @> ARRAY[sc.ticker]
                WHERE na.id = ANY(:ids)
                ORDER BY na.published_at DESC
            """)
        else:
            pg_query = text(f"""
                SELECT * FROM {table}
                WHERE id = ANY(:ids)
                ORDER BY id
            """)
        
        results = db.session.execute(pg_query, {"ids": record_ids}).fetchall()
        
        return {
            "source": "hybrid",
            "total": es_results['total'],
            "results": [dict(row._mapping) for row in results],
            "sources": ["elasticsearch", "postgresql"],
            "es_took_ms": es_results.get('took_ms', 0)
        }


# 全局实例
query_router = QueryRouter()
