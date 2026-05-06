"""
EIA (U.S. Energy Information Administration) 能源数据源
EIA Open Data - 石油、天然气、电力、煤炭等能源数据
API文档: https://www.eia.gov/opendata/v2/
"""
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, date

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


# EIA 关键指标
EIA_KEY_SERIES = {
    # 石油
    "PET.RWTC.D": {"name": "WTI Crude Oil Spot Price", "name_cn": "WTI原油现货价格", "unit": "USD/bbl", "category": "petroleum"},
    "PET.RBRTE.D": {"name": "Brent Crude Oil Spot Price", "name_cn": "布伦特原油价格", "unit": "USD/bbl", "category": "petroleum"},
    "PET.RGASUS.D": {"name": "US Regular Gasoline Price", "name_cn": "美国汽油价格", "unit": "USD/gal", "category": "petroleum"},
    "PET.EMD_EPD2D_PTG_NUS_DPG.W": {"name": "US Diesel Prices", "name_cn": "美国柴油价格", "unit": "USD/gal", "category": "petroleum"},
    # 天然气
    "NG.RNGWHHD.D": {"name": "Henry Hub Natural Gas Spot Price", "name_cn": "亨利港天然气价格", "unit": "USD/MMBtu", "category": "natural_gas"},
    # 电力
    "ELEC.GEN.ALL-US-99.M": {"name": "US Total Electricity Generation", "name_cn": "美国总发电量", "unit": "MWh", "category": "electricity"},
    "ELEC.PRICE.US-Average.csv": {"name": "US Average Electricity Price", "name_cn": "美国平均电价", "unit": "USD/kWh", "category": "electricity"},
}


class EIAProvider(BaseDataSource):
    """EIA 能源数据源"""

    name = "Macro/EIA"
    BASE_URL = "https://api.eia.gov/v2/"
    WPSR_URL = "https://ir.eia.gov/wpsr/"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'QuantDinger/1.0',
            'Accept': 'application/json',
        })
        # EIA API 限流: 5000次/小时
        self._limiter = RateLimiter(min_interval=0.1, jitter_min=0.05, jitter_max=0.15)
        self._cache: Dict[str, Any] = {}

    def _resolve_api_key(self) -> str:
        """解析 API Key"""
        try:
            key = ConfigResolver.get_api_key("macro_eia", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("EIA_API_KEY", "").strip()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """发送请求到 EIA API"""
        if not self._api_key:
            logger.warning("[EIA] API key not configured")
            return None

        self._limiter.wait()

        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        params["api_key"] = self._api_key

        try:
            resp = self._session.get(url, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[EIA] Request failed: {endpoint} - {e}")
            return None

    def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> Optional[Dict]:
        """
        获取 EIA 时间序列数据

        Args:
            series_id: 系列ID (如 PET.RWTC.D)
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回条数
        """
        params = {
            "frequency": "daily",
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": limit,
        }

        if start_date:
            params["start"] = start_date.replace("-", "")
        if end_date:
            params["end"] = end_date.replace("-", "")

        # 解析 series_id
        parts = series_id.split(".")
        if len(parts) >= 2:
            category = ".".join(parts[:2])
            endpoint = f"{category}/data/"
            params["facets[seriesId][]"] = series_id
            return self._make_request(endpoint, params)

        return None

    def get_key_indicators(self, limit: int = 10) -> Dict[str, Any]:
        """
        获取关键能源指标

        Args:
            limit: 返回指标数量
        """
        result = {}
        series_list = list(EIA_KEY_SERIES.keys())[:limit]

        for series_id in series_list:
            cache_key = f"eia_indicator:{series_id}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if time.time() - cached.get("_ts", 0) < 3600:
                    result[series_id] = cached
                    continue

            data = self.get_series(series_id, limit=1)
            if data and "response" in data:
                try:
                    items = data["response"].get("data", [])
                    if items:
                        item = items[0]
                        result[series_id] = {
                            "name": EIA_KEY_SERIES[series_id]["name"],
                            "name_cn": EIA_KEY_SERIES[series_id]["name_cn"],
                            "value": item.get("value"),
                            "date": item.get("period"),
                            "unit": EIA_KEY_SERIES[series_id]["unit"],
                            "_ts": time.time(),
                        }
                        self._cache[cache_key] = result[series_id]
                except (KeyError, TypeError, IndexError) as e:
                    logger.debug(f"[EIA] Failed to parse {series_id}: {e}")

        return result

    def get_petroleum_stocks(self, product: str = "WCRFIRS") -> Dict[str, Any]:
        """
        获取石油库存数据

        Args:
            product: 产品代码 (如 WCRFIRS = 原油库存)
        """
        if not self._api_key:
            return {}

        endpoint = f"petroleum/{product}/data/"
        params = {
            "frequency": "weekly",
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 10,
            "api_key": self._api_key,
        }

        return self._make_request(endpoint, params) or {}

    def get_natural_gas_storage(self) -> Dict[str, Any]:
        """获取天然气库存数据"""
        if not self._api_key:
            return {}

        endpoint = "natural-gas/ngp/data/"
        params = {
            "frequency": "weekly",
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 10,
            "api_key": self._api_key,
        }

        return self._make_request(endpoint, params) or {}

    def get_spot_prices(self, product: str = "crude") -> Dict[str, Any]:
        """
        获取现货价格

        Args:
            product: 产品类型 (crude, gasoline, diesel, propane)
        """
        if product == "crude":
            series = "PET.RWTC.D"
        elif product == "brent":
            series = "PET.RBRTE.D"
        elif product == "gasoline":
            series = "PET.RGASUS.D"
        elif product == "diesel":
            series = "PET.EMD_EPD2D_PTG_NUS_DPG.W"
        elif product == "natural_gas":
            series = "NG.RNGWHHD.D"
        else:
            series = "PET.RWTC.D"

        return self.get_series(series, limit=1) or {}

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """
        获取时间序列数据

        Args:
            symbol: 系列ID (如 PET.RWTC.D)
            timeframe: 时间周期
            limit: 返回条数
            before_time: 获取此时间之前的数据
        """
        series_id = symbol.upper() if symbol.upper() in EIA_KEY_SERIES else symbol

        # 转换时间周期
        freq_map = {
            "1m": "minute",
            "5m": "minute",
            "15m": "minute",
            "30m": "minute",
            "1H": "hourly",
            "4H": "hourly",
            "1D": "daily",
            "1W": "weekly",
            "1M": "monthly",
        }
        frequency = freq_map.get(timeframe, "daily")

        params = {
            "frequency": frequency,
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": limit,
        }

        # 添加 series_id facet
        parts = series_id.split(".")
        if len(parts) >= 2:
            category = ".".join(parts[:2])
            endpoint = f"{category}/data/"
            params["facets[seriesId][]"] = series_id
            data = self._make_request(endpoint, params)
        else:
            data = None

        klines = []
        if data and "response" in data:
            try:
                items = data["response"].get("data", [])
                for item in items:
                    period = item.get("period", "")
                    value = item.get("value")
                    if not period or value is None:
                        continue

                    dt = self._parse_period(period)
                    if dt:
                        ts = int(dt.timestamp())
                        klines.append(self.format_kline(ts, value, value, value, value, 0))
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"[EIA] Kline parse error: {e}")

        return self.filter_and_limit(klines, limit, before_time)

    def _parse_period(self, period: str) -> Optional[datetime]:
        """解析 EIA 时间格式"""
        if not period:
            return None
        try:
            return datetime.fromisoformat(period.replace("/", "-"))
        except (ValueError, TypeError):
            try:
                return datetime.strptime(period, "%Y%m%d")
            except (ValueError, TypeError):
                try:
                    return datetime.strptime(period, "%Y-%m-%d")
                except (ValueError, TypeError):
                    return None

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取最新能源价格"""
        series_id = symbol.upper() if symbol.upper() in EIA_KEY_SERIES else symbol

        data = self.get_series(series_id, limit=1)
        if data and "response" in data:
            try:
                items = data["response"].get("data", [])
                if items:
                    item = items[0]
                    return {
                        "last": float(item.get("value", 0)),
                        "symbol": symbol,
                        "date": item.get("period"),
                        "source": "EIA",
                    }
            except (KeyError, TypeError, ValueError, IndexError):
                pass

        return {"last": 0, "symbol": symbol}