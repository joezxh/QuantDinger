"""
Elasticsearch 客户端封装
"""
from elasticsearch import Elasticsearch, helpers
from flask import current_app
import json
import logging

logger = logging.getLogger(__name__)


class ESClient:
    """Elasticsearch 客户端单例"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = None
        return cls._instance
    
    @property
    def client(self):
        if self._client is None:
            es_hosts = current_app.config.get('ELASTICSEARCH_HOSTS', ['http://localhost:9200'])
            self._client = Elasticsearch(es_hosts)
        return self._client
    
    def init_indices(self):
        """初始化所有索引"""
        indices = {
            'news_articles': {
                'settings': {
                    'number_of_shards': 3,
                    'number_of_replicas': 1,
                    'refresh_interval': '5s'
                },
                'mappings': {
                    'properties': {
                        'article_id': {'type': 'keyword'},
                        'title': {
                            'type': 'text',
                            'analyzer': 'standard',
                            'fields': {
                                'keyword': {'type': 'keyword', 'ignore_above': 256}
                            }
                        },
                        'content': {'type': 'text', 'analyzer': 'standard'},
                        'summary': {'type': 'text', 'analyzer': 'standard'},
                        'symbols': {'type': 'keyword'},
                        'categories': {'type': 'keyword'},
                        'sentiment_score': {'type': 'float'},
                        'importance_score': {'type': 'float'},
                        'published_at': {'type': 'date'},
                        'source': {'type': 'keyword'},
                        'author': {'type': 'keyword'}
                    }
                }
            },
            'security_companies': {
                'settings': {
                    'number_of_shards': 2,
                    'number_of_replicas': 1
                },
                'mappings': {
                    'properties': {
                        'company_id': {'type': 'keyword'},
                        'ticker': {'type': 'keyword'},
                        'company_name': {
                            'type': 'text',
                            'analyzer': 'standard',
                            'fields': {
                                'keyword': {'type': 'keyword'},
                                'suggest': {'type': 'completion'}
                            }
                        },
                        'sector': {'type': 'keyword'},
                        'industry': {'type': 'keyword'},
                        'exchange': {'type': 'keyword'},
                        'market_cap': {'type': 'long'},
                        'description': {'type': 'text'}
                    }
                }
            },
            'institution_entities': {
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 1
                },
                'mappings': {
                    'properties': {
                        'institution_id': {'type': 'keyword'},
                        'standard_name': {
                            'type': 'text',
                            'analyzer': 'standard',
                            'fields': {
                                'keyword': {'type': 'keyword'},
                                'suggest': {'type': 'completion'}
                            }
                        },
                        'aliases': {'type': 'keyword'},
                        'institution_type': {'type': 'keyword'},
                        'cik': {'type': 'keyword'},
                        'total_companies_held': {'type': 'integer'},
                        'total_market_value': {'type': 'double'},
                        'country': {'type': 'keyword'}
                    }
                }
            },
            'polymarket_users': {
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 1
                },
                'mappings': {
                    'properties': {
                        'user_id': {'type': 'keyword'},
                        'primary_wallet': {'type': 'keyword'},
                        'display_name': {
                            'type': 'text',
                            'fields': {
                                'keyword': {'type': 'keyword'},
                                'suggest': {'type': 'completion'}
                            }
                        },
                        'linked_wallets': {'type': 'keyword'},
                        'total_volume': {'type': 'double'},
                        'total_trades': {'type': 'integer'},
                        'win_rate': {'type': 'float'}
                    }
                }
            }
        }
        
        for index_name, config in indices.items():
            try:
                if not self.client.indices.exists(index=index_name):
                    self.client.indices.create(index=index_name, body=config)
                    logger.info(f"Created ES index: {index_name}")
                else:
                    logger.info(f"ES index already exists: {index_name}")
            except Exception as e:
                logger.error(f"Failed to create ES index {index_name}: {e}")
    
    def index_document(self, index: str, doc_id: str, document: dict):
        """索引单个文档"""
        try:
            return self.client.index(index=index, id=doc_id, document=document)
        except Exception as e:
            logger.error(f"ES index error: {e}")
            raise
    
    def bulk_index(self, actions: list):
        """批量索引"""
        try:
            success, errors = helpers.bulk(self.client, actions, chunk_size=500)
            return success, errors
        except Exception as e:
            logger.error(f"ES bulk error: {e}")
            raise
    
    def search(self, index: str, query: dict, size: int = 10, **kwargs):
        """搜索"""
        try:
            return self.client.search(index=index, query=query, size=size, **kwargs)
        except Exception as e:
            logger.error(f"ES search error: {e}")
            raise
    
    def delete_document(self, index: str, doc_id: str):
        """删除文档"""
        try:
            return self.client.delete(index=index, id=doc_id, ignore=[404])
        except Exception as e:
            logger.error(f"ES delete error: {e}")
            raise


# 全局实例
es_client = ESClient()
