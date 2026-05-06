"""
IMF (International Monetary Fund) 宏观数据源
IMF Data API - 国际金融、GDP、通胀、国际收支数据
API文档: https://dataservices.imf.org/REST/SDMX_JSON.svc/
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


# IMF 关键指标映射
IMF_INDICATORS = {
    "GDP": {"name": "GDP (Current USD)", "name_cn": "名义GDP", "unit": "USD"},
    "NGDP_RPCH": {"name": "Real GDP Growth", "name_cn": "实际GDP增长率", "unit": "%"},
    "PCPIPCH": {"name": "Inflation Rate", "name_cn": "通胀率", "unit": "%"},
    "BCA": {"name": "Current Account Balance", "name_cn": "经常账户余额", "unit": "USD"},
    "LUR": {"name": "Unemployment Rate", "name_cn": "失业率", "unit": "%"},
    "GGXWDG_NGDP": {"name": "Government Debt", "name_cn": "政府债务/GDP", "unit": "%"},
    "BCABP6": {"name": "BOP Current Account", "name_cn": "国际收支经常账户", "unit": "USD"},
}

# 国家代码映射
COUNTRY_CODES = {
    "US": "USA", "CN": "CHN", "JP": "JPN", "DE": "DEU", "FR": "FRA",
    "GB": "GBR", "IN": "IND", "IT": "ITA", "CA": "CAN", "KR": "KOR",
    "BR": "BRA", "AU": "AUS", "MX": "MEX", "RU": "RUS", "ES": "ESP",
}


class IMFProvider(BaseDataSource):
    """IMF 宏观经济数据源"""

    name = "Macro/IMF"
    BASE_URL = "http://dataservices.imf.org/REST/SDMX_JSON.svc"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'QuantDinger/1.0'
        })
        self._limiter = RateLimiter(min_interval=1.0, jitter_min=0.3, jitter_max=0.7)
        self._cache: Dict[str, Any] = {}

    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """发送请求到 IMF API"""
        self._limiter.wait()
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[IMF] Request failed: {endpoint} - {e}")
            return None

    def get_indicator(
        self,
        indicator: str = "NGDP_RPCH",
        country: str = "USA",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100
    ) -> Optional[Dict]:
        """
        获取 IMF 指定指标数据

        Args:
            indicator: 指标代码 (如 NGDP_RPCH, PCPIPCH, BCA)
            country: 国家代码 (如 USA, CHN, JPN)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            limit: 返回条数
        """
        # IMF SDMX JSON 格式的 endpoint
        freq = "Q"  # 季度数据
        date_range = ""
        if start_date and end_date:
            date_range = f"?startPeriod={start_date}&endPeriod={end_date}"

        endpoint = f"CompactData/{country}/{freq}.{indicator}.{date_range}"
        data = self._make_request(endpoint)

        if not data or "CompactData" not in data:
            return None

        return data

    def get_key_indicators(self, country: str = "USA", limit: int = 10) -> Dict[str, Any]:
        """
        获取关键宏观指标

        Args:
            country: 国家代码 (如 USA)
            limit: 返回指标数量
        """
        result = {}
        indicators = list(IMF_INDICATORS.keys())[:limit]

        for ind in indicators:
            cache_key = f"imf_indicator:{country}:{ind}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if time.time() - cached.get("_ts", 0) < 3600:
                    result[ind] = cached
                    continue

            data = self.get_indicator(ind, country, limit=1)
            if data and "CompactData" in data:
                try:
                    obs = data["CompactData"][f"{country}"][f"{ind}"]["Obs"]
                    if isinstance(obs, list) and len(obs) > 0:
                        latest = obs[-1]
                        val = latest.get("ObsValue")
                        result[ind] = {
                            "name": IMF_INDICATORS[ind]["name"],
                            "name_cn": IMF_INDICATORS[ind]["name_cn"],
                            "value": float(val) if val else None,
                            "date": latest.get("TimePeriod"),
                            "unit": IMF_INDICATORS[ind]["unit"],
                            "_ts": time.time(),
                        }
                        self._cache[cache_key] = result[ind]
                except (KeyError, TypeError, ValueError) as e:
                    logger.debug(f"[IMF] Failed to parse {ind}: {e}")

        return result

    def get_bop_data(
        self,
        country: str = "USA",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取国际收支数据"""
        date_range = ""
        if start_date and end_date:
            date_range = f"?startPeriod={start_date}&endPeriod={end_date}"

        endpoint = f"CompactData/DP/{country}.{date_range}"
        return self._make_request(endpoint) or {}

    def get_gdp_growth(self, countries: List[str] = None, limit: int = 20) -> Dict[str, Any]:
        """获取实际GDP增长率 (多个国家)"""
        if countries is None:
            countries = ["USA", "CHN", "JPN", "DEU", "FRA", "GBR"]

        result = {}
        for country in countries[:limit]:
            data = self.get_indicator("NGDP_RPCH", country, limit=1)
            if data and "CompactData" in data:
                try:
                    obs = data["CompactData"][f"{country}"]["NGDP_RPCH"]["Obs"]
                    if isinstance(obs, list) and len(obs) > 0:
                        latest = obs[-1]
                        result[country] = {
                            "value": float(latest.get("ObsValue", 0)),
                            "date": latest.get("TimePeriod"),
                        }
                except (KeyError, TypeError):
                    pass
        return result

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """获取时间序列数据"""
        # symbol 格式: "INDICATOR:COUNTRY" 如 "NGDP_RPCH:USA"
        parts = symbol.upper().split(":")
        if len(parts) < 2:
            parts = [parts[0], "USA"]

        indicator, country = parts[0], parts[1]

        data = self.get_indicator(indicator, country, limit=limit)
        if not data or "CompactData" not in data:
            return []

        klines = []
        try:
            obs_list = data["CompactData"][country][indicator]["Obs"]
            if isinstance(obs_list, dict):
                obs_list = [obs_list]

            for obs in obs_list:
                period = obs.get("TimePeriod", "")
                val = obs.get("ObsValue")
                if val is None:
                    continue

                # 解析时期 (Q1 2023 -> 2023-03-31)
                dt = self._parse_period(period)
                if dt is None:
                    continue

                ts = int(dt.timestamp())
                fval = float(val)

                klines.append(self.format_kline(ts, fval, fval, fval, fval, 0))
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"[IMF] Failed to parse kline data: {e}")

        return self.filter_and_limit(klines, limit, before_time)

    def _parse_period(self, period: str) -> Optional[datetime]:
        """解析 IMF 时间格式 (如 2023-Q1, 2023M01)"""
        if not period:
            return None
        try:
            # 季度格式: 2023-Q1
            if "-Q" in period:
                year, q = period.split("-Q")
                month = (int(q) - 1) * 3 + 2
                return datetime(int(year), month, 1)
            # 月度格式: 2023M01
            if "M" in period:
                parts = period.split("M")
                return datetime(int(parts[0]), int(parts[1]), 1)
            # 年份格式: 2023
            return datetime(int(period), 1, 1)
        except (ValueError, IndexError):
            return None

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取最新指标值"""
        parts = symbol.upper().split(":")
        indicator = parts[0] if parts else "NGDP_RPCH"
        country = parts[1] if len(parts) > 1 else "USA"

        data = self.get_indicator(indicator, country, limit=1)
        if data and "CompactData" in data:
            try:
                obs = data["CompactData"][country][indicator]["Obs"]
                if isinstance(obs, list) and len(obs) > 0:
                    latest = obs[-1]
                    return {
                        "last": float(latest.get("ObsValue", 0)),
                        "symbol": symbol,
                        "date": latest.get("TimePeriod"),
                        "source": "IMF",
                    }
            except (KeyError, TypeError, ValueError):
                pass
        return {"last": 0, "symbol": symbol}