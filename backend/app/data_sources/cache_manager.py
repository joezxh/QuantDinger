# -*- coding: utf-8 -*-
"""
===================================
数据缓存管理模块 (多级缓存)
===================================

缓存层级:
  L0: 内存 (OrderedDict, LRU) -- 始终可用，最快
  L1: Redis                    -- 可用时使用，支持跨进程共享
  L2: PostgreSQL (qd_data_cache) -- 持久化缓存，Redis miss 后回查

TTL 按数据类型分级 (参考 DATA_SOURCE_INTEGRATION_PLAN 2.2.4):
  - 实时行情: 5~10s
  - K线数据: 5s~300s (按周期分级)
  - 新闻: 900s (15min)
  - 基本面: 86400s (24h)
  - 宏观: 3600s (1h)

Redis 不可用时自动降级到 L0 内存缓存。
"""

import json
import time
import logging
import os
from typing import Dict, Any, Optional, List
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

# ============================================
# TTL 分级配置 (秒)
# ============================================
TTL_CONFIG = {
    # 实时行情 - 极短缓存
    "ticker": 10,
    "ticker_crypto": 5,

    # K线数据 - 按周期分级
    "kline_1m": 5,
    "kline_5m": 30,
    "kline_15m": 300,
    "kline_1H": 300,
    "kline_1D": 300,

    # 新闻 - 中等缓存
    "news": 900,            # 15分钟
    "news_cn": 600,         # 10分钟

    # 基本面 - 长缓存
    "fundamentals": 86400,   # 24小时
    "financial_statements": 86400,

    # 宏观 - 极长缓存
    "macro": 3600,           # 1小时
    "economic_calendar": 1800,

    # 预测市场
    "polymarket": 300,       # 5分钟

    # DeFi
    "defi_tvl": 300,

    # CFTC
    "cftc_cot": 3600,
}


def get_ttl_for_key(key: str) -> float:
    """根据缓存键推断 TTL"""
    key_lower = key.lower()
    for pattern, ttl in TTL_CONFIG.items():
        if pattern in key_lower:
            return ttl
    return 300  # 默认5分钟


# ============================================
# Redis 连接辅助
# ============================================

_redis_available: Optional[bool] = None
_redis_client = None
_redis_lock = threading.Lock()


def _get_redis_client():
    """获取 Redis 客户端（懒初始化）"""
    global _redis_available, _redis_client

    if _redis_available is False:
        return None

    if _redis_client is not None:
        return _redis_client

    with _redis_lock:
        if _redis_available is False:
            return None
        if _redis_client is not None:
            return _redis_client

        try:
            import redis
            host = os.getenv('REDIS_HOST', 'localhost')
            port = int(os.getenv('REDIS_PORT', '6379'))
            password = os.getenv('REDIS_PASSWORD') or None
            db_num = int(os.getenv('REDIS_DB', '0'))
            _redis_client = redis.Redis(
                host=host, port=port, password=password,
                db=db_num, decode_responses=True,
                socket_timeout=5, socket_connect_timeout=3,
            )
            _redis_client.ping()
            _redis_available = True
            logger.info(f"[Cache] Redis connected: {host}:{port}/{db_num}")
            return _redis_client
        except Exception as e:
            _redis_available = False
            _redis_client = None
            logger.debug(f"[Cache] Redis unavailable, using in-memory cache: {e}")
            return None


def _pg_cache_get(key: str) -> Optional[Any]:
    """从 PostgreSQL qd_data_cache 表读取缓存"""
    try:
        from app.utils.db_postgres import execute_sql
        row = execute_sql(
            "SELECT data FROM qd_data_cache WHERE cache_key = %s AND expires_at > NOW()",
            (key,), fetch="one",
        )
        if row and row.get("data"):
            return row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
    except Exception as e:
        logger.debug(f"[Cache] PG L2 get failed for {key}: {e}")
    return None


def _pg_cache_set(key: str, value: Any, ttl: float):
    """写入 PostgreSQL qd_data_cache 表"""
    try:
        from app.utils.db_postgres import execute_sql
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        data_json = json.dumps(value, default=str)
        execute_sql(
            """INSERT INTO qd_data_cache (cache_key, data, expires_at)
               VALUES (%s, %s, %s)
               ON CONFLICT (cache_key) DO UPDATE SET
                 data = EXCLUDED.data,
                 expires_at = EXCLUDED.expires_at,
                 created_at = NOW()""",
            (key, data_json, expires_at),
            fetch=None,
        )
    except Exception as e:
        logger.debug(f"[Cache] PG L2 set failed for {key}: {e}")


def _pg_cache_cleanup():
    """清理过期的 PG 缓存条目"""
    try:
        from app.utils.db_postgres import execute_sql
        execute_sql("DELETE FROM qd_data_cache WHERE expires_at < NOW()", fetch=None)
    except Exception:
        pass


@dataclass
class CacheEntry:
    """缓存条目"""
    data: Any
    timestamp: float
    ttl: float
    hit_count: int = 0
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() - self.timestamp > self.ttl
    
    def age(self) -> float:
        """返回缓存年龄（秒）"""
        return time.time() - self.timestamp


class DataCache:
    """
    多级数据缓存管理器

    缓存层级: L0(内存) -> L1(Redis) -> L2(PostgreSQL)
    读取顺序: L0 -> L1 -> L2
    写入顺序: L0 + L1 + L2 (同时写入所有层级)

    特性:
    - TTL 过期机制
    - 最大容量限制 (L0)
    - LRU 淘汰策略 (L0)
    - 线程安全
    - Redis 不可用时自动降级到内存缓存
    """

    def __init__(
        self,
        name: str = "default",
        default_ttl: float = 600.0,  # 默认10分钟
        max_size: int = 1000,         # 最大缓存条目数 (L0)
        enable_l1: bool = True,       # 启用 L1 (Redis)
        enable_l2: bool = True,       # 启用 L2 (PostgreSQL)
    ):
        self.name = name
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.enable_l1 = enable_l1
        self.enable_l2 = enable_l2
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # 统计信息
        self._hits = 0
        self._misses = 0
        self._l1_hits = 0
        self._l2_hits = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存数据（多级查询）

        查询顺序: L0(内存) -> L1(Redis) -> L2(PostgreSQL)
        L1/L2 命中后自动回填到更高级别缓存。

        Returns:
            缓存的数据，不存在或过期返回 None
        """
        # --- L0: 内存 ---
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    self._cache.move_to_end(key)
                    entry.hit_count += 1
                    self._hits += 1
                    return entry.data
                else:
                    del self._cache[key]

        # --- L1: Redis ---
        if self.enable_l1:
            try:
                r = _get_redis_client()
                if r:
                    redis_key = f"qd:{self.name}:{key}"
                    data = r.get(redis_key)
                    if data is not None:
                        value = json.loads(data)
                        self._l1_hits += 1
                        # 回填 L0
                        self.set(key, value, ttl_override=300)  # L0 用较短 TTL
                        logger.debug(f"[缓存L1命中] {self.name}:{key}")
                        return value
            except Exception as e:
                logger.debug(f"[缓存] L1 get failed: {e}")

        # --- L2: PostgreSQL ---
        if self.enable_l2:
            try:
                value = _pg_cache_get(f"{self.name}:{key}")
                if value is not None:
                    self._l2_hits += 1
                    # 回填 L0 和 L1
                    self.set(key, value, ttl_override=300)
                    logger.debug(f"[缓存L2命中] {self.name}:{key}")
                    return value
            except Exception as e:
                logger.debug(f"[缓存] L2 get failed: {e}")

        self._misses += 1
        return None
    
    def set(
        self,
        key: str,
        data: Any,
        ttl: Optional[float] = None,
        ttl_override: Optional[float] = None,
    ) -> None:
        """
        设置缓存数据（多级写入）

        同时写入 L0(内存)、L1(Redis)、L2(PostgreSQL)。

        Args:
            key: 缓存键
            data: 缓存数据
            ttl: 过期时间（秒），None 使用默认值
            ttl_override: 回填时使用的较短 TTL（内部使用）
        """
        actual_ttl = ttl_override if ttl_override is not None else (ttl if ttl is not None else self.default_ttl)

        # --- L0: 内存 ---
        with self._lock:
            while len(self._cache) >= self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
            self._cache[key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=actual_ttl,
            )

        # --- L1: Redis ---
        if self.enable_l1 and ttl_override is None:  # 回填时不写 L1/L2（避免循环）
            try:
                r = _get_redis_client()
                if r:
                    redis_key = f"qd:{self.name}:{key}"
                    r.setex(redis_key, int(actual_ttl), json.dumps(data, default=str))
            except Exception as e:
                logger.debug(f"[缓存] L1 set failed: {e}")

        # --- L2: PostgreSQL ---
        if self.enable_l2 and ttl_override is None:
            try:
                # 仅对长 TTL 的数据写入 PG（短 TTL 数据不值得持久化）
                if actual_ttl >= 300:
                    _pg_cache_set(f"{self.name}:{key}", data, actual_ttl)
            except Exception as e:
                logger.debug(f"[缓存] L2 set failed: {e}")
    
    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"[缓存] {self.name}:{key} 已删除")
                return True
            return False
    
    def clear(self) -> int:
        """清空缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"[缓存] {self.name} 已清空 {count} 条记录")
            return count
    
    def cleanup_expired(self) -> int:
        """清理过期条目"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"[缓存] {self.name} 清理 {len(expired_keys)} 条过期记录")
            return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            return {
                'name': self.name,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'l1_hits': self._l1_hits,
                'l2_hits': self._l2_hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.1%}",
                'default_ttl': self.default_ttl,
            }


# ============================================
# 全局缓存实例
# ============================================

# 实时行情缓存（10s TTL, L1+L2 启用）
_realtime_cache = DataCache(
    name="realtime",
    default_ttl=10.0,    # 10秒
    max_size=6000,
    enable_l2=False,     # 短 TTL 不写 PG
)

# K线数据缓存（5分钟 TTL, 全层级）
_kline_cache = DataCache(
    name="kline",
    default_ttl=300.0,   # 5分钟
    max_size=500,
)

# 股票基本信息缓存（1天 TTL, 全层级）
_stock_info_cache = DataCache(
    name="stock_info",
    default_ttl=86400.0,  # 24小时
    max_size=6000,
)

# 宏观数据缓存（1小时 TTL, 全层级）
_macro_cache = DataCache(
    name="macro",
    default_ttl=3600.0,  # 1小时
    max_size=200,
)

# 新闻缓存（15分钟 TTL, L1+L2）
_news_cache = DataCache(
    name="news",
    default_ttl=900.0,   # 15分钟
    max_size=1000,
)


def get_realtime_cache() -> DataCache:
    """获取实时行情缓存"""
    return _realtime_cache


def get_kline_cache() -> DataCache:
    """获取K线数据缓存"""
    return _kline_cache


def get_stock_info_cache() -> DataCache:
    """获取股票信息缓存"""
    return _stock_info_cache


def get_macro_cache() -> DataCache:
    """获取宏观数据缓存"""
    return _macro_cache


def get_news_cache() -> DataCache:
    """获取新闻数据缓存"""
    return _news_cache


def cleanup_all_caches() -> Dict[str, int]:
    """清理所有缓存的过期条目"""
    result = {}
    for cache in [_realtime_cache, _kline_cache, _stock_info_cache, _macro_cache, _news_cache]:
        result[cache.name] = cache.cleanup_expired()
    # 同时清理 PG 缓存
    _pg_cache_cleanup()
    return result


def generate_kline_cache_key(
    symbol: str,
    timeframe: str,
    limit: int,
    before_time: Optional[int] = None
) -> str:
    """
    生成K线缓存键
    
    格式: symbol:timeframe:limit[:before_time]
    """
    key = f"{symbol}:{timeframe}:{limit}"
    if before_time:
        key += f":{before_time}"
    return key
