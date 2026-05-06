"""
数据源优先级路由器
根据数据类别管理多数据源的优先级、故障转移和负载均衡
"""
import time
import threading
from typing import Dict, List, Any, Optional, Type
from enum import Enum

from app.data_sources.base import BaseDataSource
from app.data_sources.circuit_breaker import CircuitBreaker
from app.data_sources.cache_manager import DataCache, get_kline_cache, get_realtime_cache
from app.data_sources.config_resolver import ConfigResolver
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataCategory(str, Enum):
    CRYPTO = "Crypto"
    US_STOCK = "USStock"
    CN_STOCK = "CNStock"
    HK_STOCK = "HKStock"
    FOREX = "Forex"
    FUTURES = "Futures"
    MACRO = "Macro"
    NEWS = "News"
    FUNDAMENTALS = "Fundamentals"
    PREDICTION_MARKET = "PredictionMarket"
    ALTERNATIVE = "Alternative"


class ProviderEntry:
    """数据源注册条目"""

    def __init__(
        self,
        provider: BaseDataSource,
        category: str,
        priority: int = 0,
        source_code: str = "",
    ):
        self.provider = provider
        self.category = category
        self.priority = priority
        self.source_code = source_code or provider.name

    def __repr__(self):
        return f"ProviderEntry({self.source_code}, category={self.category}, priority={self.priority})"


class PriorityRouter:
    """
    数据源优先级路由器

    按 market category 维护有序数据源列表，支持：
    1. 按优先级依次尝试各数据源
    2. 通过 CircuitBreaker 自动跳过熔断数据源
    3. 请求失败时自动降级到下一个优先级数据源
    4. 从数据库读取数据源配置动态调整优先级
    """

    def __init__(self, circuit_breaker: Optional[CircuitBreaker] = None):
        self._entries: Dict[str, List[ProviderEntry]] = {}
        self._lock = threading.RLock()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self._kline_cache = get_kline_cache()
        self._realtime_cache = get_realtime_cache()

    def register(
        self,
        category: str,
        provider: BaseDataSource,
        priority: int = 0,
        source_code: str = "",
    ):
        """注册数据源到指定类别"""
        with self._lock:
            entry = ProviderEntry(provider, category, priority, source_code)
            if category not in self._entries:
                self._entries[category] = []
            self._entries[category].append(entry)
            self._entries[category].sort(key=lambda e: e.priority, reverse=True)
            logger.info(f"[Router] 注册数据源: {entry.source_code} -> {category} (priority={priority})")

    def unregister(self, category: str, source_code: str):
        """移除数据源"""
        with self._lock:
            if category in self._entries:
                self._entries[category] = [
                    e for e in self._entries[category] if e.source_code != source_code
                ]

    def get_providers(self, category: str) -> List[ProviderEntry]:
        """获取指定类别的所有已注册数据源（按优先级排序）"""
        with self._lock:
            return list(self._entries.get(category, []))

    def route_kline(
        self,
        category: str,
        symbol: str,
        timeframe: str,
        limit: int,
        before_time: Optional[int] = None,
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        按优先级路由K线请求

        尝试顺序：缓存 -> 最高优先级数据源 -> 次优先级 -> ...
        """
        cache_key = f"{category}:{symbol}:{timeframe}:{limit}"
        if before_time:
            cache_key += f":{before_time}"

        if use_cache:
            cached = self._kline_cache.get(cache_key)
            if cached is not None:
                return cached

        entries = self.get_providers(category)
        last_error = None

        for entry in entries:
            if not self.circuit_breaker.is_available(entry.source_code):
                logger.debug(f"[Router] 跳过熔断数据源: {entry.source_code}")
                continue

            try:
                result = entry.provider.get_kline(symbol, timeframe, limit, before_time)
                if result:
                    self.circuit_breaker.record_success(entry.source_code)
                    if use_cache:
                        self._kline_cache.set(cache_key, result)
                    return result
            except Exception as e:
                self.circuit_breaker.record_failure(entry.source_code, str(e))
                last_error = str(e)
                logger.warning(f"[Router] {entry.source_code} K线获取失败: {e}, 尝试下一个数据源")
                continue

        logger.error(f"[Router] 所有数据源均失败: {category}:{symbol} ({last_error})")
        return []

    def route_ticker(
        self,
        category: str,
        symbol: str,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        按优先级路由实时报价请求
        """
        cache_key = f"ticker:{category}:{symbol}"

        if use_cache:
            cached = self._realtime_cache.get(cache_key)
            if cached is not None:
                return cached

        entries = self.get_providers(category)
        last_error = None
        default_ticker = {"last": 0, "symbol": symbol}

        for entry in entries:
            if not self.circuit_breaker.is_available(entry.source_code):
                continue

            try:
                result = entry.provider.get_ticker(symbol)
                if result and result.get("last"):
                    self.circuit_breaker.record_success(entry.source_code)
                    if use_cache:
                        self._realtime_cache.set(cache_key, result, ttl=10)
                    return result
            except Exception as e:
                self.circuit_breaker.record_failure(entry.source_code, str(e))
                last_error = str(e)
                logger.warning(f"[Router] {entry.source_code} ticker获取失败: {e}")
                continue

        logger.error(f"[Router] 所有数据源均失败: ticker:{category}:{symbol} ({last_error})")
        return default_ticker

    def route_method(
        self,
        category: str,
        method_name: str,
        **kwargs,
    ) -> Any:
        """
        按优先级路由任意方法调用

        用于调用 provider 上的特定方法（如 get_fundamentals, get_news 等）
        """
        entries = self.get_providers(category)

        for entry in entries:
            if not self.circuit_breaker.is_available(entry.source_code):
                continue

            method = getattr(entry.provider, method_name, None)
            if method is None:
                continue

            try:
                result = method(**kwargs)
                if result is not None:
                    self.circuit_breaker.record_success(entry.source_code)
                    return result
            except Exception as e:
                self.circuit_breaker.record_failure(entry.source_code, str(e))
                logger.warning(f"[Router] {entry.source_code}.{method_name} 失败: {e}")
                continue

        return None

    def get_status(self) -> Dict[str, Any]:
        """获取路由器状态"""
        return {
            "categories": {
                cat: [
                    {
                        "source_code": e.source_code,
                        "priority": e.priority,
                        "provider_name": e.provider.name,
                    }
                    for e in entries
                ]
                for cat, entries in self._entries.items()
            },
            "circuit_breaker": self.circuit_breaker.get_status(),
        }


# ============================================
# 全局路由器实例
# ============================================

_global_router: Optional[PriorityRouter] = None
_router_lock = threading.Lock()


def get_router() -> PriorityRouter:
    """获取全局路由器实例（懒初始化）"""
    global _global_router
    if _global_router is not None:
        return _global_router

    with _router_lock:
        if _global_router is not None:
            return _global_router

        from app.data_sources.circuit_breaker import get_realtime_circuit_breaker
        _global_router = PriorityRouter(
            circuit_breaker=get_realtime_circuit_breaker()
        )
        _register_default_providers(_global_router)
        return _global_router


def _register_default_providers(router: PriorityRouter):
    """注册默认数据源到路由器"""
    try:
        from app.data_sources.crypto import CryptoDataSource
        router.register(DataCategory.CRYPTO, CryptoDataSource(), priority=100, source_code="crypto_ccxt")
    except Exception as e:
        logger.warning(f"Failed to register CryptoDataSource: {e}")

    try:
        from app.data_sources.us_stock import USStockDataSource
        router.register(DataCategory.US_STOCK, USStockDataSource(), priority=50, source_code="us_stock_yfinance")
    except Exception as e:
        logger.warning(f"Failed to register USStockDataSource: {e}")

    try:
        from app.data_sources.cn_stock import CNStockDataSource
        router.register(DataCategory.CN_STOCK, CNStockDataSource(), priority=50, source_code="cn_stock_akshare")
    except Exception as e:
        logger.warning(f"Failed to register CNStockDataSource: {e}")

    try:
        from app.data_sources.hk_stock import HKStockDataSource
        router.register(DataCategory.HK_STOCK, HKStockDataSource(), priority=50, source_code="hk_stock_akshare")
    except Exception as e:
        logger.warning(f"Failed to register HKStockDataSource: {e}")

    try:
        from app.data_sources.forex import ForexDataSource
        router.register(DataCategory.FOREX, ForexDataSource(), priority=50, source_code="forex_yfinance")
    except Exception as e:
        logger.warning(f"Failed to register ForexDataSource: {e}")

    try:
        from app.data_sources.futures import FuturesDataSource
        router.register(DataCategory.FUTURES, FuturesDataSource(), priority=50, source_code="futures_akshare")
    except Exception as e:
        logger.warning(f"Failed to register FuturesDataSource: {e}")

    try:
        from app.data_sources.polymarket import PolymarketDataSource
        router.register(DataCategory.PREDICTION_MARKET, PolymarketDataSource(), priority=100, source_code="polymarket")
    except Exception as e:
        logger.warning(f"Failed to register PolymarketDataSource: {e}")

    # 新增数据源（可选，依赖额外库）
    _try_register_optional_providers(router)

    logger.info(f"[Router] 数据源注册完成: {len(router._entries)} 个类别")


def _try_register_optional_providers(router: PriorityRouter):
    """尝试注册可选数据源（依赖额外库，注册失败不影响核心功能）"""

    try:
        from app.data_sources.providers.macro_fred import FREDProvider
        router.register(DataCategory.MACRO, FREDProvider(), priority=100, source_code="macro_fred")
    except Exception as e:
        logger.debug(f"Optional provider macro_fred not available: {e}")

    try:
        from app.data_sources.providers.cn_stock_tushare import TushareProvider
        router.register(DataCategory.CN_STOCK, TushareProvider(), priority=80, source_code="cn_stock_tushare")
    except Exception as e:
        logger.debug(f"Optional provider cn_stock_tushare not available: {e}")

    try:
        from app.data_sources.providers.cn_stock_baostock import BaoStockProvider
        router.register(DataCategory.CN_STOCK, BaoStockProvider(), priority=30, source_code="cn_stock_baostock")
    except Exception as e:
        logger.debug(f"Optional provider cn_stock_baostock not available: {e}")

    try:
        from app.data_sources.providers.crypto_coingecko import CoinGeckoProvider
        router.register(DataCategory.CRYPTO, CoinGeckoProvider(), priority=20, source_code="crypto_coingecko")
    except Exception as e:
        logger.debug(f"Optional provider crypto_coingecko not available: {e}")

    try:
        from app.data_sources.providers.crypto_defillama import DefiLlamaProvider
        router.register(DataCategory.CRYPTO, DefiLlamaProvider(), priority=15, source_code="crypto_defillama")
    except Exception as e:
        logger.debug(f"Optional provider crypto_defillama not available: {e}")

    try:
        from app.data_sources.providers.us_stock_financial_datasets import FinancialDatasetsProvider
        router.register(DataCategory.US_STOCK, FinancialDatasetsProvider(), priority=70, source_code="us_stock_financial_datasets")
    except Exception as e:
        logger.debug(f"Optional provider us_stock_financial_datasets not available: {e}")

    try:
        from app.data_sources.providers.futures_cftc import CFTCProvider
        router.register(DataCategory.FUTURES, CFTCProvider(), priority=90, source_code="futures_cftc")
    except Exception as e:
        logger.debug(f"Optional provider futures_cftc not available: {e}")

    try:
        from app.data_sources.providers.news_google import GoogleNewsProvider
        router.register(DataCategory.NEWS, GoogleNewsProvider(), priority=30, source_code="news_google")
    except Exception as e:
        logger.debug(f"Optional provider news_google not available: {e}")

    try:
        from app.data_sources.providers.news_eastmoney import EastMoneyNewsProvider
        router.register(DataCategory.NEWS, EastMoneyNewsProvider(), priority=40, source_code="news_eastmoney")
    except Exception as e:
        logger.debug(f"Optional provider news_eastmoney not available: {e}")

    try:
        from app.data_sources.providers.macro_bls import BLSProvider
        router.register(DataCategory.MACRO, BLSProvider(), priority=90, source_code="macro_bls")
    except Exception as e:
        logger.debug(f"Optional provider macro_bls not available: {e}")

    try:
        from app.data_sources.providers.macro_worldbank import WorldBankProvider
        router.register(DataCategory.MACRO, WorldBankProvider(), priority=70, source_code="macro_worldbank")
    except Exception as e:
        logger.debug(f"Optional provider macro_worldbank not available: {e}")

    try:
        from app.data_sources.providers.futures_cboe import CBOEProvider
        router.register(DataCategory.FUTURES, CBOEProvider(), priority=80, source_code="futures_cboe")
    except Exception as e:
        logger.debug(f"Optional provider futures_cboe not available: {e}")

    try:
        from app.data_sources.providers.macro_bea import BEAProvider
        router.register(DataCategory.MACRO, BEAProvider(), priority=80, source_code="macro_bea")
    except Exception as e:
        logger.debug(f"Optional provider macro_bea not available: {e}")

    try:
        from app.data_sources.providers.fundamentals_simfin import SimFinProvider
        router.register(DataCategory.FUNDAMENTALS, SimFinProvider(), priority=20, source_code="fundamentals_simfin")
    except Exception as e:
        logger.debug(f"Optional provider fundamentals_simfin not available: {e}")

    # ============================================
    # 新增数据源 (FinceptTerminal 集成)
    # ============================================

    # IMF 宏观经济数据
    try:
        from app.data_sources.providers.macro_imf import IMFProvider
        router.register(DataCategory.MACRO, IMFProvider(), priority=65, source_code="macro_imf")
    except Exception as e:
        logger.debug(f"Optional provider macro_imf not available: {e}")


    # OECD 统计数据
    try:
        from app.data_sources.providers.macro_oecd import OECDProvider
        router.register(DataCategory.MACRO, OECDProvider(), priority=60, source_code="macro_oecd")
    except Exception as e:
        logger.debug(f"Optional provider macro_oecd not available: {e}")

    # ECB 欧洲央行数据
    try:
        from app.data_sources.providers.macro_ecb import ECBProvider
        router.register(DataCategory.MACRO, ECBProvider(), priority=55, source_code="macro_ecb")
    except Exception as e:
        logger.debug(f"Optional provider macro_ecb not available: {e}")

    # EIA 能源数据
    try:
        from app.data_sources.providers.macro_eia import EIAProvider
        router.register(DataCategory.MACRO, EIAProvider(), priority=70, source_code="macro_eia")
    except Exception as e:
        logger.debug(f"Optional provider macro_eia not available: {e}")

    # WTO 贸易数据
    try:
        from app.data_sources.providers.macro_wto import WTOProvider
        router.register(DataCategory.MACRO, WTOProvider(), priority=50, source_code="macro_wto")
    except Exception as e:
        logger.debug(f"Optional provider macro_wto not available: {e}")

    # FMP 财务报表数据
    try:
        from app.data_sources.providers.fundamentals_fmp import FMPProvider
        router.register(DataCategory.FUNDAMENTALS, FMPProvider(), priority=60, source_code="fundamentals_fmp")
    except Exception as e:
        logger.debug(f"Optional provider fundamentals_fmp not available: {e}")

    # SEC EDGAR 数据
    try:
        from app.data_sources.providers.fundamentals_sec import SECProvider
        router.register(DataCategory.FUNDAMENTALS, SECProvider(), priority=55, source_code="fundamentals_sec")
    except Exception as e:
        logger.debug(f"Optional provider fundamentals_sec not available: {e}")

    # Alpha Vantage 技术指标
    try:
        from app.data_sources.providers.market_alphavantage import AlphaVantageProvider
        router.register(DataCategory.US_STOCK, AlphaVantageProvider(), priority=40, source_code="market_alphavantage")
    except Exception as e:
        logger.debug(f"Optional provider market_alphavantage not available: {e}")

    # NewsAPI 新闻数据
    try:
        from app.data_sources.providers.news_newsapi import NewsAPIProvider
        router.register(DataCategory.NEWS, NewsAPIProvider(), priority=30, source_code="news_newsapi")
    except Exception as e:
        logger.debug(f"Optional provider news_newsapi not available: {e}")
