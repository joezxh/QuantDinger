"""
缓存策略管理器
"""
import json
import logging
from typing import Any, Optional

from ..extensions import redis_client

logger = logging.getLogger(__name__)


class CacheStrategy:
    """缓存策略管理器"""
    
    CACHE_CONFIG = {
        # 热数据缓存
        'realtime_price': {'ttl': 60, 'prefix': 'price:'},
        'latest_news': {'ttl': 300, 'prefix': 'news:latest:'},
        'market_sentiment': {'ttl': 900, 'prefix': 'sentiment:'},
        
        # 查询结果缓存
        'search_results': {'ttl': 3600, 'prefix': 'search:'},
        'company_info': {'ttl': 86400, 'prefix': 'company:'},
        'institution_info': {'ttl': 86400, 'prefix': 'institution:'},
        
        # 去重缓存
        'dedup_hash': {'ttl': 604800, 'prefix': 'dedup:'},
        'imported_items': {'ttl': 604800, 'prefix': 'imported:'},
        
        # 会话缓存
        'user_session': {'ttl': 86400, 'prefix': 'session:'},
        'api_rate_limit': {'ttl': 60, 'prefix': 'rate:'}
    }
    
    def get_cached(self, cache_type: str, key: str) -> Optional[Any]:
        """获取缓存"""
        config = self.CACHE_CONFIG.get(cache_type)
        if not config:
            return None
        
        cache_key = f"{config['prefix']}{key}"
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        return None
    
    def set_cached(self, cache_type: str, key: str, value: Any):
        """设置缓存"""
        config = self.CACHE_CONFIG.get(cache_type)
        if not config:
            return
        
        cache_key = f"{config['prefix']}{key}"
        try:
            redis_client.setex(
                cache_key,
                config['ttl'],
                json.dumps(value, default=str)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def invalidate_cache(self, cache_type: str, key: str):
        """使缓存失效"""
        config = self.CACHE_CONFIG.get(cache_type)
        if not config:
            return
        
        cache_key = f"{config['prefix']}{key}"
        try:
            redis_client.delete(cache_key)
        except Exception as e:
            logger.error(f"Cache invalidate error: {e}")
    
    def invalidate_pattern(self, cache_type: str, pattern: str):
        """按模式使缓存失效"""
        config = self.CACHE_CONFIG.get(cache_type)
        if not config:
            return
        
        search_pattern = f"{config['prefix']}{pattern}*"
        try:
            keys = redis_client.keys(search_pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache invalidate pattern error: {e}")


# 全局实例
cache_strategy = CacheStrategy()
