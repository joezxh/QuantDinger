"""
ECB (European Central Bank) 宏观数据源
ECB Statistical Data Warehouse - 欧元区货币政策、外汇储备、收益率曲线数据
API文档: https://data.ecb.europa.eu/data-detail-api
"""
import os
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ECB 关键指标
ECB_INDICATORS = {
    "FX.EUR/USD.EUR.SP00.A": {"name": "EUR/USD Rate", "name_cn": "欧元/美元汇率", "unit": "USD"},
    "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_3M": {"name": "3M EUR Yield", "name_cn": "3个月欧元收益率", "unit": "%"},
    "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y": {"name": "1Y EUR Yield", "name_cn": "1年欧元收益率", "unit": "%"},
    "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_5Y": {"name": "5Y EUR Yield", "name_cn": "5年欧元收益率", "unit": "%"},
    "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y": {"name": "10Y EUR Yield", "name_cn": "10年欧元收益率", "unit": "%"},
    "RAFA_USD": {"name": "FX Reserves (USD)", "name_cn": "外汇储备(美元)", "unit": "USD"},
    "SM.B.U2.EUR.SA.EUR.EUR.LEVAT": {"name": "M2 Money Supply", "name_cn": "M2货币供应", "unit": "EUR"},
}


class ECBProvider(BaseDataSource):
    """ECB 宏观经济数据源"""

    name = "Macro/ECB"
    FX_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    DATA_URL = "https://data.ecb.europa.eu/data-detail-api"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'QuantDinger/1.0',
            'Accept': 'application/json, application/xml',
        })
        self._limiter = RateLimiter(min_interval=1.0, jitter_min=0.2, jitter_max=0.8)
        self._cache: Dict[str, Any] = {}
        self._fx_cache: Dict[str, Any] = {}

    def _make_request(self, url: str, timeout: int = 30) -> Optional[Any]:
        """发送请求到 ECB API"""
        self._limiter.wait()
        try:
            resp = self._session.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as e:
            logger.error(f"[ECB] Request failed: {url} - {e}")
            return None

    def get_fx_rates(self) -> Dict[str, Any]:
        """
        获取每日外汇参考汇率

        Returns:
            {currency: rate, ...} 基准货币为 EUR
        """
        cache_key = "ecb_fx_rates"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.get("_ts", 0) < 86400:
                return cached

        resp = self._make_request(self.FX_URL)
        if not resp:
            return {}

        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.content)

            # 定义命名空间
            namespaces = {
                'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
                'ecb': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'
            }

            # 查找时间元素
            time_elem = root.find('.//ecb:Cube[@time]', namespaces)
            if time_elem is None:
                return {}

            date = time_elem.get('time')
            rates = {"EUR": 1.0, "date": date}

            for cube in time_elem.findall('ecb:Cube', namespaces):
                currency = cube.get('currency')
                rate = float(cube.get('rate'))
                rates[currency] = rate

            rates["_ts"] = time.time()
            self._cache[cache_key] = rates
            return rates

        except Exception as e:
            logger.error(f"[ECB] Failed to parse FX XML: {e}")
            return {}

    def get_key_indicators(self, limit: int = 10) -> Dict[str, Any]:
        """获取关键宏观指标"""
        result = {}

        # 获取外汇汇率
        fx_data = self.get_fx_rates()
        if fx_data and "date" in fx_data:
            for currency in ["USD", "GBP", "JPY", "CHF", "CNY"]:
                if currency in fx_data:
                    result[f"FX_EUR_{currency}"] = {
                        "name": f"EUR/{currency} Rate",
                        "name_cn": f"欧元/{currency}汇率",
                        "value": fx_data[currency],
                        "date": fx_data["date"],
                        "unit": currency,
                    }

        return result

    def get_series_data(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        获取 ECB 时间序列数据

        Args:
            series_id: 系列ID (如 YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        """
        url = f"{self.DATA_URL}/{series_id}"
        params = {}
        if start_date:
            params["startPeriod"] = start_date
        if end_date:
            params["endPeriod"] = end_date

        resp = self._make_request(url)
        if not resp:
            return []

        result = []
        try:
            content_type = resp.headers.get('content-type', '').lower()
            if 'json' in content_type:
                data = resp.json()
                if "dataSets" in data:
                    for ds in data["dataSets"]:
                        for obs_key, obs_val in ds.get("observations", {}).items():
                            parts = obs_key.split(":")
                            if len(parts) >= 1:
                                time_period = parts[-1]
                                dt = self._parse_period(time_period)
                                if dt:
                                    result.append({
                                        "date": dt.strftime("%Y-%m-%d"),
                                        "time": int(dt.timestamp()),
                                        "value": obs_val[0] if obs_val else None,
                                    })
        except Exception as e:
            logger.error(f"[ECB] Failed to parse series data: {e}")

        return result

    def _parse_period(self, period: str) -> Optional[datetime]:
        """解析 ECB 时间格式"""
        if not period:
            return None
        try:
            # 尝试解析为日期
            return datetime.fromisoformat(period.replace("/", "-"))
        except (ValueError, TypeError):
            return None

    def get_yield_curve(self, rating: str = "aaa") -> Dict[str, Any]:
        """
        获取欧元区国债收益率曲线

        Args:
            rating: 评级 (aaa 或 all_ratings)
        """
        maturities = {
            "3M": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_3M",
            "6M": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_6M",
            "1Y": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y",
            "2Y": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y",
            "3Y": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_3Y",
            "5Y": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_5Y",
            "7Y": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_7Y",
            "10Y": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y",
            "20Y": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_20Y",
            "30Y": "YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_30Y",
        }

        result = {}
        for tenor, series_id in maturities.items():
            data = self.get_series_data(series_id, limit=1)
            if data:
                result[tenor] = data[0] if data else None
            else:
                result[tenor] = {"value": None, "date": None}

        return result

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """
        获取时间序列数据

        Args:
            symbol: 系列ID (如 EUR/USD, 10Y_YIELD)
            timeframe: 时间周期
            limit: 返回条数
            before_time: 获取此时间之前的数据
        """
        # 解析 symbol
        symbol_upper = symbol.upper()

        # 外汇汇率
        if "/" in symbol_upper:
            parts = symbol_upper.split("/")
            base = parts[0]
            quote = parts[1]

            fx_data = self.get_fx_rates()
            if quote in fx_data and base == "EUR":
                # EUR 为基准，返回历史（ECB 主要提供当前汇率）
                rate = fx_data[quote]
                ts = int(time.time())
                return [self.format_kline(ts, rate, rate, rate, rate, 0)]

        # 收益率曲线
        if "YIELD" in symbol_upper or symbol_upper.endswith("Y"):
            tenor_map = {
                "3M": "3M", "6M": "6M", "1Y": "1Y", "2Y": "2Y",
                "3Y": "3Y", "5Y": "5Y", "7Y": "7Y", "10Y": "10Y",
                "20Y": "20Y", "30Y": "30Y"
            }
            for tenor, _ in tenor_map.items():
                if tenor in symbol_upper:
                    data = self.get_series_data(f"YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_{tenor}", limit=limit)
                    klines = []
                    for item in data:
                        ts = item.get("time", 0)
                        val = item.get("value", 0)
                        if ts and val:
                            klines.append(self.format_kline(ts, val, val, val, val, 0))
                    return self.filter_and_limit(klines, limit, before_time)

        return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取最新汇率或收益率"""
        symbol_upper = symbol.upper()

        # 外汇汇率
        if "/" in symbol_upper:
            parts = symbol_upper.split("/")
            quote = parts[1] if len(parts) > 1 else "USD"

            fx_data = self.get_fx_rates()
            if quote in fx_data:
                return {
                    "last": fx_data[quote],
                    "symbol": symbol,
                    "date": fx_data.get("date"),
                    "source": "ECB",
                }

        return {"last": 0, "symbol": symbol}