# -*- coding: utf-8 -*-
"""
===================================
令牌桶限流器 (Token Bucket Rate Limiter)
===================================

每个 Provider 独立限流，保护 API 配额不被超用。

特点：
1. 令牌桶算法：以固定速率填充令牌，每次请求消耗一个令牌
2. 支持突发：令牌桶容量 = rate，允许短时间内的突发请求
3. 线程安全：使用 threading.Lock 保护令牌操作
4. 阻塞等待：acquire() 会等待令牌可用（而非直接拒绝）
5. 非阻塞检查：try_acquire() 不等待，返回是否有令牌
6. 支持数据库配置：可从 data_rate_limit_configs 表动态加载配置

与 rate_limiter.py 的关系：
- RateLimiter（最小间隔+抖动）：用于反爬虫场景，防止被封IP
- TokenBucketRateLimiter（令牌桶）：用于API配额保护，确保不超限
"""
import time
import threading
from typing import Dict, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================
# 默认限流配置
# ============================================

_DEFAULT_LIMITER_CONFIGS = {
    # 加密货币
    "crypto_ccxt": {"rate": 60, "period": 60},
    "crypto_coingecko": {"rate": 30, "period": 60},
    "crypto_defillama": {"rate": 60, "period": 60},
    # 美股
    "us_stock_yfinance": {"rate": 60, "period": 60},
    "us_stock_finnhub": {"rate": 60, "period": 60},
    "us_stock_financial_datasets": {"rate": 60, "period": 60},
    "market_alphavantage": {"rate": 75, "period": 60},
    # A股
    "cn_stock_akshare": {"rate": 30, "period": 60},
    "cn_stock_tushare": {"rate": 500, "period": 60},
    "cn_stock_baostock": {"rate": 120, "period": 60},
    # 宏观经济
    "macro_fred": {"rate": 120, "period": 60},
    "macro_bls": {"rate": 60, "period": 60},
    "macro_worldbank": {"rate": 60, "period": 60},
    "macro_imf": {"rate": 30, "period": 60},
    "macro_oecd": {"rate": 30, "period": 60},
    "macro_ecb": {"rate": 30, "period": 60},
    "macro_eia": {"rate": 60, "period": 60},
    "macro_wto": {"rate": 30, "period": 60},
    "macro_bea": {"rate": 60, "period": 60},
    # 期货
    "futures_cftc": {"rate": 30, "period": 60},
    "futures_cboe": {"rate": 30, "period": 60},
    # 基本面
    "fundamentals_simfin": {"rate": 120, "period": 60},
    "fundamentals_fmp": {"rate": 250, "period": 60},
    "fundamentals_sec": {"rate": 10, "period": 60},
    # 新闻
    "news_google": {"rate": 10, "period": 60},
    "news_eastmoney": {"rate": 30, "period": 60},
    "news_newsapi": {"rate": 100, "period": 60},
}


class TokenBucketRateLimiter:
    """
    令牌桶限流器

    算法：
    - 桶容量 = rate（即一个周期内允许的最大请求数）
    - 令牌以 rate/period 的速率匀速填充
    - 每次请求消耗 1 个令牌
    - 桶满时停止填充，桶空时请求需等待

    Args:
        provider_name: 数据源名称（用于日志）
        rate: 每个周期允许的请求数
        period: 周期（秒），默认60秒
        burst: 突发容量，默认等于rate
    """

    def __init__(
        self,
        provider_name: str,
        rate: int,
        period: int = 60,
        burst: Optional[int] = None,
    ):
        self.provider_name = provider_name
        self.rate = rate
        self.period = period
        self.burst = burst or rate  # 默认桶容量 = rate
        self._tokens = float(rate)  # 初始满桶
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

        # 统计
        self._total_acquired = 0
        self._total_waited = 0
        self._total_wait_time_ms = 0.0

    def _refill(self):
        """填充令牌（内部方法，需在锁内调用）"""
        now = time.monotonic()
        elapsed = now - self._last_refill
        # 计算应填充的令牌数
        tokens_to_add = elapsed * (self.rate / self.period)
        self._tokens = min(self.burst, self._tokens + tokens_to_add)
        self._last_refill = now

    def acquire(self, timeout: float = 30.0) -> bool:
        """
        获取一个令牌（阻塞等待）

        如果当前无令牌可用，会等待直到令牌填充或超时。

        Args:
            timeout: 最大等待时间（秒），0表示不等待

        Returns:
            True 表示获取成功，False 表示超时未获取
        """
        with self._lock:
            self._refill()

            if self._tokens >= 1.0:
                self._tokens -= 1.0
                self._total_acquired += 1
                return True

            # 计算需要等待的时间
            wait_time = (1.0 - self._tokens) * (self.period / self.rate)

        # 在锁外等待（避免阻塞其他线程）
        if wait_time > timeout:
            logger.warning(
                f"[TokenBucket] {self.provider_name}: 需等待 {wait_time:.1f}s "
                f"超过超时 {timeout:.1f}s，请求被限流"
            )
            return False

        time.sleep(wait_time)

        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                self._total_acquired += 1
                self._total_waited += 1
                self._total_wait_time_ms += wait_time * 1000
                return True

            # 极端情况下令牌仍不足（并发竞争），重试
            self._tokens -= 1.0
            self._total_acquired += 1
            self._total_waited += 1
            self._total_wait_time_ms += wait_time * 1000
            return True

    def try_acquire(self) -> bool:
        """
        尝试获取一个令牌（非阻塞）

        Returns:
            True 表示获取成功，False 表示无令牌可用
        """
        with self._lock:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                self._total_acquired += 1
                return True
            return False

    def get_status(self) -> Dict[str, any]:
        """获取限流器状态"""
        with self._lock:
            self._refill()
            return {
                "provider_name": self.provider_name,
                "rate": self.rate,
                "period": self.period,
                "burst": self.burst,
                "current_tokens": round(self._tokens, 2),
                "total_acquired": self._total_acquired,
                "total_waited": self._total_waited,
                "avg_wait_ms": round(
                    self._total_wait_time_ms / self._total_waited, 1
                ) if self._total_waited > 0 else 0,
            }


# ============================================
# 全局限流器管理器
# ============================================

class RateLimiterManager:
    """
    限流器管理器

    集中管理所有 Provider 的令牌桶限流器，
    根据 data_data_source_configs 表的配置动态创建。
    """

    def __init__(self):
        self._limiters: Dict[str, TokenBucketRateLimiter] = {}
        self._lock = threading.Lock()

    def get_limiter(
        self,
        provider_name: str,
        rate: int = 60,
        period: int = 60,
    ) -> TokenBucketRateLimiter:
        """获取或创建指定 Provider 的限流器"""
        if provider_name not in self._limiters:
            with self._lock:
                if provider_name not in self._limiters:
                    self._limiters[provider_name] = TokenBucketRateLimiter(
                        provider_name=provider_name,
                        rate=rate,
                        period=period,
                    )
        return self._limiters[provider_name]

    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有限流器状态"""
        return {
            name: limiter.get_status()
            for name, limiter in self._limiters.items()
        }


# 全局管理器实例
_rate_limiter_manager = RateLimiterManager()


def get_rate_limiter_manager() -> RateLimiterManager:
    """获取全局限流器管理器"""
    return _rate_limiter_manager


def get_default_limiter(provider_name: str) -> TokenBucketRateLimiter:
    """获取预配置的限流器"""
    config = _DEFAULT_LIMITER_CONFIGS.get(provider_name, {"rate": 60, "period": 60})
    return _rate_limiter_manager.get_limiter(
        provider_name,
        rate=config["rate"],
        period=config["period"],
    )


def get_limiter_from_database(provider_name: str, db_session) -> Optional[TokenBucketRateLimiter]:
    """
    从数据库加载限流配置并创建限流器

    Args:
        provider_name: 数据源名称
        db_session: 数据库会话

    Returns:
        配置好的 TokenBucketRateLimiter，或 None（如果未找到配置）
    """
    try:
        from app.models.data_source_meta import DataSourceConfig, DataSourceRateLimitConfig

        # 查找数据源配置
        source_config = db_session.query(DataSourceConfig).filter(
            DataSourceConfig.source_code == provider_name
        ).first()

        if not source_config:
            logger.debug(f"[TokenBucket] 未找到数据源配置: {provider_name}")
            return None

        # 查找限流配置
        rate_limit_config = db_session.query(DataSourceRateLimitConfig).filter(
            DataSourceRateLimitConfig.source_config_id == source_config.id,
            DataSourceRateLimitConfig.enabled == True
        ).first()

        if not rate_limit_config:
            logger.debug(f"[TokenBucket] 未找到限流配置: {provider_name}")
            return None

        # 创建限流器
        limiter = TokenBucketRateLimiter(
            provider_name=provider_name,
            rate=rate_limit_config.rate,
            period=rate_limit_config.period,
            burst=rate_limit_config.burst or rate_limit_config.rate,
        )

        logger.info(f"[TokenBucket] 从数据库加载限流配置: {provider_name} "
                   f"(rate={rate_limit_config.rate}/{rate_limit_config.period}s)")

        return limiter

    except Exception as e:
        logger.warning(f"[TokenBucket] 从数据库加载配置失败: {e}")
        return None



def get_limiter(
    provider_name: str,
    db_session = None,
    use_database_config: bool = True
) -> TokenBucketRateLimiter:
    """
    获取限流器的统一入口

    优先从数据库加载配置（如果提供 db_session 且 use_database_config=True），
    否则使用代码中的默认配置。

    Args:
        provider_name: 数据源名称
        db_session: 数据库会话（可选）
        use_database_config: 是否优先使用数据库配置

    Returns:
        TokenBucketRateLimiter 实例
    """
    if db_session and use_database_config:
        db_limiter = get_limiter_from_database(provider_name, db_session)
        if db_limiter:
            return db_limiter

    return get_default_limiter(provider_name)
