"""
数据同步编排器（PostgreSQL → Elasticsearch）
"""
from datetime import datetime, timedelta
import json
import logging
import time
from typing import Any, Optional

from flask import current_app
from sqlalchemy import text

from .elasticsearch_client import es_client
from ..extensions import db, redis_client

logger = logging.getLogger(__name__)


class DataSyncOrchestrator:
    """数据同步编排器"""
    
    # 表名到 ES 索引的映射
    TABLE_TO_INDEX = {
        'news_articles': 'news_articles',
        'security_companies': 'security_companies',
        'entity_financial_institutions': 'institution_entities',
        'entity_polymarket_users': 'polymarket_users',
    }
    
    def sync_record(self, table_name: str, record_id: int, operation: str = 'index'):
        """
        同步单条记录到 Elasticsearch
        
        Args:
            table_name: 数据库表名
            record_id: 记录ID
            operation: index/update/delete
        """
        sync_key = f"sync:{table_name}:{record_id}"
        
        # 检查是否已同步（避免重复）
        if redis_client.get(sync_key):
            return {'status': 'skipped', 'reason': 'already_synced'}
        
        try:
            # 1. 从 PostgreSQL 读取数据
            record = self._fetch_record(table_name, record_id)
            if not record:
                return {'status': 'skipped', 'reason': 'record_not_found'}
            
            # 2. 转换为 ES 文档
            es_index = self.TABLE_TO_INDEX.get(table_name, f"pg_{table_name}")
            es_doc_id = f"{table_name}_{record_id}"
            es_document = self._transform_to_es_doc(record, table_name)
            
            # 3. 写入 Elasticsearch
            if operation == 'index':
                es_client.index_document(es_index, es_doc_id, es_document)
            elif operation == 'update':
                es_client.client.update(
                    index=es_index,
                    id=es_doc_id,
                    doc=es_document,
                    doc_as_upsert=True
                )
            elif operation == 'delete':
                es_client.delete_document(es_index, es_doc_id)
            
            # 4. 记录同步状态到 Redis（1小时过期）
            redis_client.setex(sync_key, 3600, "synced")
            
            # 5. 更新 PostgreSQL 同步状态
            self._update_sync_status(table_name, record_id, 'synced')
            
            logger.info(f"Synced {table_name}/{record_id} to ES")
            return {'status': 'success', 'index': es_index, 'doc_id': es_doc_id}
            
        except Exception as e:
            # 重试机制
            retry_count = redis_client.incr(f"retry:{sync_key}")
            if retry_count <= 3:
                # 加入重试队列（指数退避）
                retry_at = time.time() + (2 ** retry_count)
                redis_client.lpush(
                    "sync:retry_queue",
                    json.dumps({
                        "table": table_name,
                        "record_id": record_id,
                        "operation": operation,
                        "retry_at": retry_at
                    })
                )
                logger.warning(f"Sync failed for {table_name}/{record_id}, retry {retry_count}")
            else:
                # 超过重试次数，记录失败
                self._update_sync_status(table_name, record_id, 'failed')
                logger.error(f"Sync failed permanently for {table_name}/{record_id}: {e}")
            
            return {'status': 'failed', 'error': str(e), 'retry_count': retry_count}
    
    def bulk_sync(self, table_name: str, record_ids: list, operation: str = 'index'):
        """批量同步"""
        actions = []
        es_index = self.TABLE_TO_INDEX.get(table_name, f"pg_{table_name}")
        
        for record_id in record_ids:
            record = self._fetch_record(table_name, record_id)
            if not record:
                continue
            
            es_doc_id = f"{table_name}_{record_id}"
            es_document = self._transform_to_es_doc(record, table_name)
            
            action = {
                '_op_type': operation if operation != 'update' else 'index',
                '_index': es_index,
                '_id': es_doc_id,
                '_source': es_document
            }
            actions.append(action)
        
        if actions:
            success, errors = es_client.bulk_index(actions)
            logger.info(f"Bulk sync: {success} success, {len(errors)} errors")
            
            # 更新同步状态
            for record_id in record_ids:
                self._update_sync_status(table_name, record_id, 'synced')
            
            return {'success': success, 'errors': len(errors)}
        
        return {'success': 0, 'errors': 0}
    
    def incremental_sync(self, table_name: str, last_sync_time: datetime = None):
        """增量同步"""
        if last_sync_time is None:
            # 默认同步最近5分钟的数据
            last_sync_time = datetime.utcnow() - timedelta(minutes=5)
        
        try:
            query = text(f"""
                SELECT id FROM {table_name}
                WHERE updated_at > :last_sync
                ORDER BY updated_at
                LIMIT 1000
            """)
            
            results = db.session.execute(query, {"last_sync": last_sync_time}).fetchall()
            record_ids = [r[0] for r in results]
            
            if record_ids:
                self.bulk_sync(table_name, record_ids, 'update')
                
                # 更新最后同步时间
                new_sync_time = datetime.utcnow()
                redis_client.set(
                    f"sync:last:{table_name}",
                    new_sync_time.isoformat()
                )
                
                return {
                    'status': 'success',
                    'synced_count': len(record_ids),
                    'last_sync': new_sync_time.isoformat()
                }
            
            return {'status': 'success', 'synced_count': 0}
            
        except Exception as e:
            logger.error(f"Incremental sync failed for {table_name}: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def full_sync(self, table_name: str, hours: int = 24):
        """全量同步（最近 N 小时的数据）"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        try:
            query = text(f"""
                SELECT id FROM {table_name}
                WHERE created_at > :since
                ORDER BY id
            """)
            
            results = db.session.execute(query, {"since": since}).fetchall()
            record_ids = [r[0] for r in results]
            
            if record_ids:
                self.bulk_sync(table_name, record_ids, 'index')
                
                return {
                    'status': 'success',
                    'synced_count': len(record_ids),
                    'period': f"last_{hours}h"
                }
            
            return {'status': 'success', 'synced_count': 0}
            
        except Exception as e:
            logger.error(f"Full sync failed for {table_name}: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _fetch_record(self, table_name: str, record_id: int):
        """从 PostgreSQL 读取单条记录"""
        try:
            query = text(f"SELECT * FROM {table_name} WHERE id = :id")
            result = db.session.execute(query, {"id": record_id}).fetchone()
            return result
        except Exception as e:
            logger.error(f"Fetch record failed: {e}")
            return None
    
    def _update_sync_status(self, table_name: str, record_id: int, status: str):
        """更新 PostgreSQL 中的同步状态"""
        try:
            query = text(f"""
                UPDATE {table_name}
                SET es_synced = :status, es_synced_at = NOW()
                WHERE id = :id
            """)
            db.session.execute(query, {"status": status, "id": record_id})
            db.session.commit()
        except Exception as e:
            logger.error(f"Update sync status failed: {e}")
            db.session.rollback()
    
    def _transform_to_es_doc(self, record, table_name: str) -> dict:
        """转换数据库记录为 ES 文档"""
        doc = {}
        
        # 通用字段
        for key, value in record._mapping.items():
            if hasattr(value, 'isoformat'):
                doc[key] = value.isoformat()
            elif value is not None:
                doc[key] = value
        
        # 表特定转换
        if table_name == 'news_articles':
            doc['article_id'] = str(doc.get('id', ''))
        elif table_name == 'security_companies':
            doc['company_id'] = str(doc.get('id', ''))
        elif table_name == 'entity_financial_institutions':
            doc['institution_id'] = str(doc.get('id', ''))
        elif table_name == 'entity_polymarket_users':
            doc['user_id'] = str(doc.get('id', ''))
        
        # 添加索引时间
        doc['indexed_at'] = datetime.utcnow().isoformat()
        
        return doc


# 全局实例
sync_orchestrator = DataSyncOrchestrator()
