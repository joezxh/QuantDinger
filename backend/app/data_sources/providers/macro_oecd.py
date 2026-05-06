"""
OECD (Organization for Economic Co-operation and Development) 宏观数据源
OECD Statistics API - 发达国家经济指标数据
API文档: https://sdmx.oecd.org/public/rest/
"""
import os
import time
import ssl
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, date

import requests
import urllib3

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


# 国家代码映射
COUNTRY_CODES = {
    "US": "USA", "USA": "USA",
    "CN": "CHN", "CHN": "CHN", "CHINA": "CHN",
    "JP": "JPN", "JPN": "JPN", "JAPAN": "JPN",
    "DE": "DEU", "DEU": "DEU", "GERMANY": "DEU",
    "FR": "FRA", "FRA": "FRA", "FRANCE": "FRA",
    "GB": "GBR", "GBR": "GBR", "UK": "GBR",
    "IN": "IND", "IND": "IND", "INDIA": "IND",
    "IT": "ITA", "ITA": "ITA", "ITALY": "ITA",
    "CA": "CAN", "CAN": "CAN", "CANADA": "CAN",
    "KR": "KOR", "KOR": "KOR", "KOREA": "KOR",
    "BR": "BRA", "BRA": "BRA", "BRAZIL": "BRA",
    "AU": "AUS", "AUS": "AUS", "AUSTRALIA": "AUS",
    "MX": "MEX", "MEX": "MEX", "MEXICO": "MEX",
    "RU": "RUS", "RUS": "RUS", "RUSSIA": "RUS",
    "ES": "ESP", "ESP": "ESP", "SPAIN": "ESP",
    "NL": "NLD", "NLD": "NLD", "NETHERLANDS": "NLD",
    "SE": "SWE", "SWE": "SWE", "SWEDEN": "SWE",
    "CH": "CHE", "CHE": "CHE", "SWITZERLAND": "CHE",
    "G7": "G7", "G20": "G20", "OECD": "OECD",
}

# OECD 关键指标
OECD_INDICATORS = {
    "GDP": {"name": "GDP (National currency)", "name_cn": "名义GDP", "dataset": "QNA"},
    "GDP_VOL": {"name": "Real GDP", "name_cn": "实际GDP", "dataset": "QNA"},
    "CPI": {"name": "Consumer Price Index", "name_cn": "CPI", "dataset": "PRICE"},
    "URATE": {"name": "Unemployment Rate", "name_cn": "失业率", "dataset": "AES"},
    "BOP": {"name": "Balance of Payments", "name_cn": "国际收支", "dataset": "BOP"},
}


class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    """支持旧版 SSL 的 HTTP Adapter"""

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


class OECDProvider(BaseDataSource):
    """OECD 宏观经济数据源"""

    name = "Macro/OECD"
    BASE_URL_V1 = "https://sdmx.oecd.org/public/rest/"
    BASE_URL_V2 = "https://sdmx.oecd.org/public/rest/v2/"

    def __init__(self):
        # 创建支持旧版 SSL 的 session
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        self._session = requests.Session()
        self._session.mount("https://", CustomHttpAdapter(ctx))

        self._limiter = RateLimiter(min_interval=1.0, jitter_min=0.3, jitter_max=0.7)
        self._cache: Dict[str, Any] = {}

    def _make_request(
        self,
        url: str,
        params: Optional[Dict] = None,
        format_type: str = "json"
    ) -> Optional[Dict]:
        """发送请求到 OECD API"""
        self._limiter.wait()
        try:
            headers = {'Accept-Language': 'en'}
            if format_type == "json":
                headers['Accept'] = 'application/vnd.sdmx.data+json; charset=utf-8; version=2'

            resp = self._session.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()

            content_type = resp.headers.get('content-type', '').lower()
            if 'json' in content_type:
                return resp.json()

            return {"raw": resp.text}
        except Exception as e:
            logger.error(f"[OECD] Request failed: {url} - {e}")
            return None

    def _parse_oecd_date(self, date_str: str) -> Optional[datetime]:
        """解析 OECD 日期格式"""
        import pandas as pd
        if not date_str:
            return None
        try:
            if "Q" in date_str:
                return pd.to_datetime(date_str).to_period("Q").start_time
            if len(date_str) == 4:
                return datetime(int(date_str), 1, 1)
            if len(date_str) == 7:
                return pd.to_datetime(date_str).to_period("M").start_time
            return pd.to_datetime(date_str)
        except (ValueError, TypeError):
            return None

    def _normalize_country(self, country: str) -> str:
        """标准化国家代码"""
        if not country:
            return "USA"
        upper = country.upper()
        return COUNTRY_CODES.get(upper, upper)

    def get_indicator(
        self,
        indicator: str = "GDP_VOL",
        country: str = "USA",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "quarter"
    ) -> Optional[Dict]:
        """
        获取 OECD 指定指标数据

        Args:
            indicator: 指标代码 (如 GDP_VOL, CPI, URATE)
            country: 国家代码 (如 USA, GBR)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            frequency: 数据频率 (quarter, month, annual)
        """
        freq_code = {"quarter": "Q", "month": "M", "annual": "A"}.get(frequency, "Q")
        country_code = self._normalize_country(country)

        # 构建 SDMX v2 URL
        # GDP 实际值: OECD.SDD.NAD/DSD_NAMAIN1@DF_QNA
        if indicator == "GDP_VOL":
            url = (
                f"{self.BASE_URL_V2}data/dataflow/OECD.SDD.NAD/DSD_NAMAIN1@DF_QNA/1.0/"
                f"{country_code}.{freq_code}..S1..B1GQ.VOBP...EUR+_T+GBP+USD+JPY.XDC"
            )
        elif indicator == "CPI":
            url = (
                f"{self.BASE_URL_V2}data/dataflow/OECD.SDD.TPS/DSD_PRICES@DF_PRICES_ALL/1.0/"
                f"{country_code}.{freq_code}.N.CPI._T._Z._T.XDC"
            )
        elif indicator == "URATE":
            url = (
                f"{self.BASE_URL_V2}data/dataflow/OECD.SDD.STD/AES@DF_AES/1.0/"
                f"{country_code}.{freq_code}.LRUN64TT.ST.A.SA"
            )
        else:
            # 通用格式
            url = f"{self.BASE_URL_V1}data/{indicator}/{country_code}"

        params = {}
        if start_date:
            params["c[TIME_PERIOD]"] = f"ge:{start_date}"
        if end_date:
            params["c[TIME_PERIOD]"] += f"+le:{end_date}"

        data = self._make_request(url, params)
        return data

    def get_gdp_data(
        self,
        country: str = "USA",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        real: bool = True
    ) -> List[Dict]:
        """获取 GDP 数据"""
        indicator = "GDP_VOL" if real else "GDP"
        data = self.get_indicator(indicator, country, start_date, end_date)

        result = []
        if data and "data" in data:
            # 解析 JSON 数据
            try:
                datasets = data.get("dataSets", [])
                if datasets and len(datasets) > 0:
                    observations = datasets[0].get("observations", {})
                    for obs_key, obs_val in observations.items():
                        parts = obs_key.split(":")
                        if len(parts) >= 1:
                            time_period = parts[-1]
                            dt = self._parse_period(time_period)
                            if dt:
                                value = obs_val[0] if obs_val else None
                                result.append({
                                    "date": dt.strftime("%Y-%m-%d"),
                                    "time": int(dt.timestamp()),
                                    "value": float(value) if value else None,
                                })
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"[OECD] Failed to parse GDP data: {e}")

        return result

    def get_key_indicators(self, country: str = "USA", limit: int = 10) -> Dict[str, Any]:
        """获取关键宏观指标"""
        result = {}
        country_code = self._normalize_country(country)

        for ind in list(OECD_INDICATORS.keys())[:limit]:
            cache_key = f"oecd_indicator:{country_code}:{ind}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if time.time() - cached.get("_ts", 0) < 3600:
                    result[ind] = cached
                    continue

            data = self.get_indicator(ind, country_code, limit=1)
            if data and "data" in data:
                try:
                    datasets = data.get("dataSets", [])
                    if datasets and len(datasets) > 0:
                        observations = datasets[0].get("observations", {})
                        if observations:
                            latest_key = sorted(observations.keys())[-1]
                            obs_val = observations[latest_key][0]
                            time_period = latest_key.split(":")[-1]

                            result[ind] = {
                                "name": OECD_INDICATORS[ind]["name"],
                                "name_cn": OECD_INDICATORS[ind]["name_cn"],
                                "value": float(obs_val) if obs_val else None,
                                "date": time_period,
                                "_ts": time.time(),
                            }
                            self._cache[cache_key] = result[ind]
                except (KeyError, TypeError, ValueError, IndexError) as e:
                    logger.debug(f"[OECD] Failed to parse {ind}: {e}")

        return result

    def _parse_period(self, period: str) -> Optional[datetime]:
        """解析 OECD 时间格式 (如 2023-Q1, 2023-M01)"""
        import pandas as pd
        if not period:
            return None
        try:
            if "Q" in period:
                return pd.to_datetime(period).to_period("Q").start_time
            if "M" in period:
                return pd.to_datetime(period).to_period("M").start_time
            return pd.to_datetime(period)
        except (ValueError, TypeError):
            return None

    def get_cpi_data(
        self,
        country: str = "USA",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """获取 CPI 数据"""
        return self._get_series_data("CPI", country, start_date, end_date)

    def _get_series_data(
        self,
        indicator: str,
        country: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """通用时间序列数据获取"""
        data = self.get_indicator(indicator, country, start_date, end_date)
        result = []

        if data and "data" in data:
            try:
                datasets = data.get("dataSets", [])
                if datasets and len(datasets) > 0:
                    observations = datasets[0].get("observations", {})
                    for obs_key, obs_val in observations.items():
                        time_period = obs_key.split(":")[-1]
                        dt = self._parse_period(time_period)
                        if dt:
                            value = obs_val[0] if obs_val else None
                            result.append({
                                "date": dt.strftime("%Y-%m-%d"),
                                "time": int(dt.timestamp()),
                                "value": float(value) if value else None,
                            })
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"[OECD] Failed to parse series data: {e}")

        return result

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """获取时间序列数据"""
        parts = symbol.upper().split(":")
        indicator = parts[0] if parts else "GDP_VOL"
        country = self._normalize_country(parts[1] if len(parts) > 1 else "USA")

        freq = "quarter" if timeframe in ["1D", "1W", "1M"] else "month"
        data = self.get_indicator(indicator, country, limit=limit)

        klines = []
        if data and "data" in data:
            try:
                datasets = data.get("dataSets", [])
                if datasets and len(datasets) > 0:
                    observations = datasets[0].get("observations", {})
                    for obs_key, obs_val in observations.items():
                        time_period = obs_key.split(":")[-1]
                        dt = self._parse_period(time_period)
                        if dt:
                            ts = int(dt.timestamp())
                            value = obs_val[0] if obs_val else 0
                            klines.append(self.format_kline(ts, value, value, value, value, 0))
            except (KeyError, TypeError, ValueError) as e:
                logger.error(f"[OECD] Kline parse error: {e}")

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取最新指标值"""
        parts = symbol.upper().split(":")
        indicator = parts[0] if parts else "GDP_VOL"
        country = self._normalize_country(parts[1] if len(parts) > 1 else "USA")

        data = self.get_indicator(indicator, country, limit=1)
        if data and "data" in data:
            try:
                datasets = data.get("dataSets", [])
                if datasets and len(datasets) > 0:
                    observations = datasets[0].get("observations", {})
                    if observations:
                        latest_key = sorted(observations.keys())[-1]
                        obs_val = observations[latest_key][0]
                        return {
                            "last": float(obs_val) if obs_val else 0,
                            "symbol": symbol,
                            "date": latest_key.split(":")[-1],
                            "source": "OECD",
                        }
            except (KeyError, TypeError, ValueError, IndexError):
                pass

        return {"last": 0, "symbol": symbol}