"""
数据源工厂
根据市场类型返回对应的数据源，支持 PriorityRouter 多源路由

改造说明：
- get_source() 保持原有接口，内部委托给 PriorityRouter 最高优先级 Provider
- get_kline() / get_ticker() 优先使用 PriorityRouter 路由
- 新增 route() 方法直接调用路由器的任意方法
- 新增 get_provider() 获取指定类别的最高优先级 Provider
"""
from typing import Dict, List, Any, Optional

from app.data_sources.base import BaseDataSource
from app.data_sources.priority_router import get_router, DataCategory
from app.utils.logger import get_logger

logger = get_logger(__name__)

_ROUTER_ENABLED = True

# Market string -> DataCategory mapping
_MARKET_TO_CATEGORY = {
    "Crypto": DataCategory.CRYPTO,
    "USStock": DataCategory.US_STOCK,
    "CNStock": DataCategory.CN_STOCK,
    "HKStock": DataCategory.HK_STOCK,
    "Forex": DataCategory.FOREX,
    "Futures": DataCategory.FUTURES,
    "Macro": DataCategory.MACRO,
    "PredictionMarket": DataCategory.PREDICTION_MARKET,
}


class DataSourceFactory:
    """数据源工厂

    提供向后兼容的接口，内部委托给 PriorityRouter 进行多源路由。
    优先级: PriorityRouter > 单数据源回退
    """

    _sources: Dict[str, BaseDataSource] = {}

    @classmethod
    def get_source(cls, market: str) -> BaseDataSource:
        """获取指定市场的数据源实例。

        优先返回 PriorityRouter 中注册的最高优先级 Provider；
        如无路由注册则回退到单数据源创建。
        """
        if _ROUTER_ENABLED:
            try:
                router = get_router()
                category = _MARKET_TO_CATEGORY.get(market)
                if category:
                    providers = router.get_providers(category.value)
                    if providers:
                        return providers[0].provider
            except Exception as e:
                logger.debug(f"Router get_source fallback: {e}")

        # Fallback: create single source directly
        if market not in cls._sources:
            cls._sources[market] = cls._create_source(market)
        return cls._sources[market]

    @classmethod
    def get_data_source(cls, name: str) -> BaseDataSource:
        key = (name or "").strip().lower()
        if key in ("crypto", "binance", "okx", "bybit", "bitget", "kucoin", "gate", "mexc", "kraken", "coinbase"):
            return cls.get_source("Crypto")
        if key in ("futures",):
            return cls.get_source("Futures")
        return cls.get_source("Crypto")

    @classmethod
    def get_provider(cls, category: DataCategory, method_name: str, **kwargs) -> Any:
        """直接通过路由器调用指定类别数据源的方法。

        这是新的统一入口，推荐新代码使用此方法。

        Args:
            category: 数据类别
            method_name: 方法名（如 get_fundamentals, get_news 等）
            **kwargs: 方法参数

        Returns:
            方法调用结果，或 None（所有数据源失败时）
        """
        try:
            router = get_router()
            return router.route_method(category.value, method_name, **kwargs)
        except Exception as e:
            logger.error(f"route_method failed: {category.value}.{method_name} - {e}")
            return None

    @classmethod
    def route(cls, market: str, method_name: str, **kwargs) -> Any:
        """通过市场名称调用路由器方法（便捷方法）。

        Args:
            market: 市场名称（如 'Crypto', 'USStock'）
            method_name: 方法名
            **kwargs: 方法参数
        """
        category = _MARKET_TO_CATEGORY.get(market)
        if not category:
            logger.warning(f"Unknown market: {market}")
            return None
        return cls.get_provider(category, method_name, **kwargs)

    @classmethod
    def _create_source(cls, market: str) -> BaseDataSource:
        """创建单个数据源实例（回退方法）"""
        if market == 'Crypto':
            from app.data_sources.crypto import CryptoDataSource
            return CryptoDataSource()
        elif market == 'CNStock':
            from app.data_sources.cn_stock import CNStockDataSource
            return CNStockDataSource()
        elif market == 'HKStock':
            from app.data_sources.hk_stock import HKStockDataSource
            return HKStockDataSource()
        elif market == 'USStock':
            from app.data_sources.us_stock import USStockDataSource
            return USStockDataSource()
        elif market == 'Forex':
            from app.data_sources.forex import ForexDataSource
            return ForexDataSource()
        elif market == 'Futures':
            from app.data_sources.futures import FuturesDataSource
            return FuturesDataSource()
        else:
            raise ValueError(f"不支持的市场类型: {market}")

    @classmethod
    def get_kline(
        cls,
        market: str,
        symbol: str,
        timeframe: str,
        limit: int,
        before_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        if _ROUTER_ENABLED:
            try:
                from app.data_sources.priority_router import get_router
                router = get_router()
                klines = router.route_kline(market, symbol, timeframe, limit, before_time)
                if klines:
                    klines.sort(key=lambda x: x['time'])
                    return klines
            except Exception as e:
                logger.debug(f"Router fallback to single source: {e}")

        try:
            source = cls.get_source(market)
            klines = source.get_kline(symbol, timeframe, limit, before_time)
            klines.sort(key=lambda x: x['time'])
            return klines
        except Exception as e:
            logger.error(f"Failed to fetch K-lines {market}:{symbol} - {str(e)}")
            return []

    @classmethod
    def get_ticker(cls, market: str, symbol: str) -> Dict[str, Any]:
        if _ROUTER_ENABLED:
            try:
                from app.data_sources.priority_router import get_router
                router = get_router()
                result = router.route_ticker(market, symbol)
                if result and result.get("last"):
                    return result
            except Exception as e:
                logger.debug(f"Router fallback to single source: {e}")

        try:
            source = cls.get_source(market)
            return source.get_ticker(symbol)
        except NotImplementedError:
            logger.warning(f"get_ticker not implemented for market: {market}")
            return {'last': 0, 'symbol': symbol}
        except Exception as e:
            logger.error(f"Failed to fetch ticker {market}:{symbol} - {str(e)}")
            return {'last': 0, 'symbol': symbol}

