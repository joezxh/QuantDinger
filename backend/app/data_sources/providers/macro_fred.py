"""
FRED (Federal Reserve Economic Data) 宏观数据源
美联储官方经济数据库，提供利率、就业、CPI、GDP等关键宏观指标
API文档: https://fred.stlouisfed.org/docs/api/fred/
"""
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


FRED_KEY_SERIES = {
    "DFF": {"name": "Federal Funds Effective Rate", "name_cn": "联邦基金利率", "unit": "%"},
    "DGS10": {"name": "10-Year Treasury Rate", "name_cn": "10年期国债收益率", "unit": "%"},
    "DGS2": {"name": "2-Year Treasury Rate", "name_cn": "2年期国债收益率", "unit": "%"},
    "T10Y2Y": {"name": "10Y-2Y Spread", "name_cn": "10Y-2Y利差(衰退指标)", "unit": "%"},
    "CPIAUCSL": {"name": "CPI All Urban", "name_cn": "CPI消费者物价指数", "unit": "Index"},
    "CPILFESL": {"name": "Core CPI", "name_cn": "核心CPI", "unit": "Index"},
    "UNRATE": {"name": "Unemployment Rate", "name_cn": "失业率", "unit": "%"},
    "PAYEMS": {"name": "Nonfarm Payrolls", "name_cn": "非农就业", "unit": "Thousand"},
    "GDP": {"name": "GDP", "name_cn": "GDP", "unit": "Bil.$"},
    "GDPC1": {"name": "Real GDP", "name_cn": "实际GDP", "unit": "Bil.$"},
    "FEDFUNDS": {"name": "Federal Funds Rate (Monthly)", "name_cn": "联邦基金利率(月)", "unit": "%"},
    "M2SL": {"name": "M2 Money Stock", "name_cn": "M2货币供应", "unit": "Bil.$"},
    "PCE": {"name": "PCE Price Index", "name_cn": "PCE物价指数", "unit": "Index"},
    "PCEPI": {"name": "PCE Price Index (Chain-type)", "name_cn": "链式PCE物价指数", "unit": "Index"},
    "RSAFS": {"name": "Retail Sales", "name_cn": "零售销售", "unit": "Mil.$"},
    "HOUST": {"name": "Housing Starts", "name_cn": "新屋开工", "unit": "Thousand"},
    "INDPRO": {"name": "Industrial Production Index", "name_cn": "工业生产指数", "unit": "Index"},
    "UMCSENT": {"name": "Consumer Sentiment", "name_cn": "消费者信心指数", "unit": "Index"},
    "VIXCLS": {"name": "CBOE Volatility Index (VIX)", "name_cn": "VIX波动率指数", "unit": "%"},
    "DTWEXBGS": {"name": "Trade Weighted USD Index", "name_cn": "美元指数(贸易加权)", "unit": "Index"},
}


class FREDProvider(BaseDataSource):
    """FRED 宏观经济数据源"""

    name = "Macro/FRED"
    BASE_URL = "https://api.stlouisfed.org/fred"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._limiter = RateLimiter(min_interval=0.5, jitter_min=0.2, jitter_max=0.8)
        self._cache: Dict[str, Any] = {}

    def _resolve_api_key(self) -> str:
        try:
            key = ConfigResolver.get_api_key("macro_fred", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("FRED_API_KEY", "").strip()

    def _request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict]:
        if not self._api_key:
            logger.warning("[FRED] API key not configured")
            return None

        params["api_key"] = self._api_key
        params["file_type"] = "json"

        self._limiter.wait()

        try:
            resp = self._session.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[FRED] Request failed: {endpoint} - {e}")
            return None

    def get_series(
        self,
        series_id: str,
        observation_start: Optional[str] = None,
        observation_end: Optional[str] = None,
        limit: int = 100,
        sort_order: str = "desc",
    ) -> Optional[Dict]:
        """
        获取FRED时间序列数据

        Args:
            series_id: 序列ID，如 'DFF', 'CPIAUCSL'
            observation_start: 起始日期 YYYY-MM-DD
            observation_end: 结束日期 YYYY-MM-DD
            limit: 返回条数
            sort_order: 'desc' 或 'asc'
        """
        params = {
            "series_id": series_id,
            "limit": limit,
            "sort_order": sort_order,
        }
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end

        return self._request("series/observations", params)

    def get_key_indicators(self, limit: int = 10) -> Dict[str, Any]:
        """
        获取关键宏观指标最新值

        Returns:
            {series_id: {name, name_cn, value, date, unit}, ...}
        """
        result = {}
        for sid, meta in list(FRED_KEY_SERIES.items())[:limit]:
            cache_key = f"fred_indicator:{sid}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if time.time() - cached.get("_ts", 0) < 3600:
                    result[sid] = cached
                    continue

            data = self.get_series(sid, limit=1, sort_order="desc")
            if data and data.get("observations"):
                obs = data["observations"][0]
                val = obs.get("value")
                result[sid] = {
                    "name": meta["name"],
                    "name_cn": meta["name_cn"],
                    "value": float(val) if val and val != "." else None,
                    "date": obs.get("date"),
                    "unit": meta["unit"],
                    "_ts": time.time(),
                }
                self._cache[cache_key] = result[sid]
            else:
                result[sid] = {
                    "name": meta["name"],
                    "name_cn": meta["name_cn"],
                    "value": None,
                    "date": None,
                    "unit": meta["unit"],
                }

        return result

    def get_yield_curve(self) -> Dict[str, Any]:
        """获取国债收益率曲线关键点位"""
        yield_series = {
            "DGS1": "1Y",
            "DGS2": "2Y",
            "DGS3": "3Y",
            "DGS5": "5Y",
            "DGS7": "7Y",
            "DGS10": "10Y",
            "DGS20": "20Y",
            "DGS30": "30Y",
        }
        result = {}
        for sid, tenor in yield_series.items():
            data = self.get_series(sid, limit=1, sort_order="desc")
            if data and data.get("observations"):
                obs = data["observations"][0]
                val = obs.get("value")
                result[tenor] = {
                    "yield": float(val) if val and val != "." else None,
                    "date": obs.get("date"),
                }
        return result

    # BaseDataSource interface (FRED不直接提供K线，但可作为宏观数据辅助)
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        series_id = symbol.upper()
        if series_id not in FRED_KEY_SERIES:
            return []

        end_ts = before_time or int(time.time())
        end_dt = datetime.fromtimestamp(end_ts)
        observation_end = end_dt.strftime("%Y-%m-%d")

        data = self.get_series(series_id, observation_end=observation_end, limit=limit, sort_order="desc")
        if not data or not data.get("observations"):
            return []

        klines = []
        for obs in reversed(data["observations"]):
            val = obs.get("value")
            if val and val != ".":
                dt = datetime.strptime(obs["date"], "%Y-%m-%d")
                ts = int(dt.timestamp())
                fval = float(val)
                klines.append(self.format_kline(ts, fval, fval, fval, fval, 0))

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        data = self.get_series(symbol.upper(), limit=1, sort_order="desc")
        if data and data.get("observations"):
            obs = data["observations"][0]
            val = obs.get("value")
            return {
                "last": float(val) if val and val != "." else None,
                "symbol": symbol,
                "date": obs.get("date"),
                "source": "FRED",
            }
        return {"last": 0, "symbol": symbol}
