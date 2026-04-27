"""
查询缓存服务
管理 QueryCache 的读写、过期清理和去重控制
"""
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from app.database.session import get_session
from app.models.data_source_meta import QueryCache
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QueryCacheService:
    """查询缓存服务"""

    def get_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """通过 cache_key 获取缓存"""
        with get_session() as session:
            cache = session.query(QueryCache).filter(
                QueryCache.cache_key == cache_key
            ).first()
            if not cache:
                return None
            # 检查是否过期
            if cache.expires_at and cache.expires_at < datetime.now(timezone.utc):
                cache.status = "expired"
                session.flush()
                return self._to_dict(cache)
            return self._to_dict(cache)

    def find_active_cache(
        self,
        source_code: str,
        query_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """查找活跃的缓存（用于去重）"""
        cache_key = self._generate_cache_key(source_code, query_params)
        cache = self.get_cache(cache_key)
        if not cache:
            return None
        # 只有 completed 状态的缓存才是有效的结果缓存
        if cache.get("status") == "completed" and cache.get("result_data"):
            # 更新请求计数
            with get_session() as session:
                db_cache = session.query(QueryCache).filter(
                    QueryCache.cache_key == cache_key
                ).first()
                if db_cache:
                    db_cache.request_count += 1
                    db_cache.last_requested_at = datetime.now(timezone.utc)
                    session.flush()
            return cache
        # pending / running 状态表示有请求正在执行，返回去重用
        if cache.get("status") in ("pending", "running"):
            return cache
        return None

    def create_pending_cache(
        self,
        source_code: str,
        query_params: Dict[str, Any],
        ttl_seconds: int = 300
    ) -> Dict[str, Any]:
        """创建待处理的缓存条目（用于去重控制）"""
        cache_key = self._generate_cache_key(source_code, query_params)
        with get_session() as session:
            # 检查是否已有缓存
            existing = session.query(QueryCache).filter(
                QueryCache.cache_key == cache_key
            ).first()
            if existing:
                return self._to_dict(existing)

            expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
            cache = QueryCache(
                cache_key=cache_key,
                source_code=source_code,
                query_params=query_params,
                status="pending",
                ttl_seconds=ttl_seconds,
                expires_at=expires_at,
            )
            session.add(cache)
            session.flush()
            logger.debug(f"Created pending cache: {cache_key[:16]}...")
            return self._to_dict(cache)

    def update_cache_result(
        self,
        cache_key: str,
        result_data: Any,
        status: str = "completed",
        error_message: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """更新缓存结果"""
        with get_session() as session:
            cache = session.query(QueryCache).filter(
                QueryCache.cache_key == cache_key
            ).first()
            if not cache:
                logger.warning(f"Cache not found for update: {cache_key[:16]}...")
                return None

            cache.result_data = result_data
            cache.status = status
            cache.error_message = error_message

            if status == "completed":
                cache.completed_at = datetime.now(timezone.utc)
                # 估算结果大小
                try:
                    cache.result_size_bytes = len(json.dumps(result_data).encode("utf-8"))
                except Exception:
                    cache.result_size_bytes = 0
            elif status == "failed":
                cache.error_message = error_message

            cache.last_requested_at = datetime.now(timezone.utc)
            session.flush()
            logger.debug(f"Updated cache: {cache_key[:16]}... status={status}")
            return self._to_dict(cache)

    def set_running(self, cache_key: str) -> bool:
        """将缓存状态设为 running"""
        with get_session() as session:
            cache = session.query(QueryCache).filter(
                QueryCache.cache_key == cache_key
            ).first()
            if not cache:
                return False
            cache.status = "running"
            session.flush()
            return True

    def delete_cache(self, cache_id: int) -> bool:
        """删除缓存"""
        with get_session() as session:
            cache = session.query(QueryCache).filter(QueryCache.id == cache_id).first()
            if not cache:
                return False
            session.delete(cache)
            logger.info(f"Deleted cache: id={cache_id}")
            return True

    def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """清理过期的缓存条目"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        with get_session() as session:
            count = session.query(QueryCache).filter(
                (QueryCache.expires_at < datetime.now(timezone.utc)) |
                (QueryCache.created_at < cutoff)
            ).delete(synchronize_session=False)
            logger.info(f"Cleaned up {count} expired cache entries")
            return count

    def list_cache(
        self,
        source_code: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """列出缓存条目"""
        with get_session() as session:
            query = session.query(QueryCache)
            if source_code:
                query = query.filter(QueryCache.source_code == source_code)
            if status:
                query = query.filter(QueryCache.status == status)

            total = query.count()
            items = query.order_by(QueryCache.id.desc()).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return {
                "items": [self._to_dict(item) for item in items],
                "total": total,
                "page": page,
                "page_size": page_size
            }

    def _generate_cache_key(self, source_code: str, query_params: Dict[str, Any]) -> str:
        """生成确定性的缓存键（SHA-256）"""
        # 规范化：排序键、统一类型
        normalized = json.dumps(query_params, sort_keys=True, ensure_ascii=False, default=str)
        payload = f"{source_code}:{normalized}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _to_dict(self, cache: QueryCache) -> Dict[str, Any]:
        return {
            "id": cache.id,
            "cache_key": cache.cache_key,
            "dataset_id": cache.dataset_id,
            "source_code": cache.source_code,
            "query_params": cache.query_params,
            "result_data": cache.result_data,
            "result_size_bytes": cache.result_size_bytes,
            "status": cache.status,
            "error_message": cache.error_message,
            "request_count": cache.request_count,
            "ttl_seconds": cache.ttl_seconds,
            "expires_at": cache.expires_at.isoformat() if cache.expires_at else None,
            "first_requested_at": cache.first_requested_at.isoformat() if cache.first_requested_at else None,
            "last_requested_at": cache.last_requested_at.isoformat() if cache.last_requested_at else None,
            "completed_at": cache.completed_at.isoformat() if cache.completed_at else None,
            "created_at": cache.created_at.isoformat() if cache.created_at else None,
            "updated_at": cache.updated_at.isoformat() if cache.updated_at else None,
        }


# Singleton
_query_cache_service: Optional[QueryCacheService] = None


def get_query_cache_service() -> QueryCacheService:
    global _query_cache_service
    if _query_cache_service is None:
        _query_cache_service = QueryCacheService()
    return _query_cache_service
