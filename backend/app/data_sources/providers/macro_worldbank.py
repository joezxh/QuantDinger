"""
世界银行宏观数据源
提供全球各国GDP、人口、贸易等宏观经济指标
API文档: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


WB_KEY_INDICATORS = {
    "NY.GDP.MKTP.CD": {"name": "GDP (current US$)", "name_cn": "GDP(现价美元)"},
    "NY.GDP.MKTP.KD.ZG": {"name": "GDP growth (annual %)", "name_cn": "GDP增长率"},
    "FP.CPI.TOTL.ZG": {"name": "Inflation, CPI (annual %)", "name_cn": "通胀率"},
    "SL.UEM.TOTL.ZS": {"name": "Unemployment (% of labor force)", "name_cn": "失业率"},
    "NE.TRD.GNFS.ZS": {"name": "Trade (% of GDP)", "name_cn": "贸易占GDP比"},
    "SP.POP.TOTL": {"name": "Population, total", "name_cn": "总人口"},
    "BX.KLT.DINV.WD.GD.ZS": {"name": "FDI, net inflows (% of GDP)", "name_cn": "FDI净流入占GDP比"},
    "GC.DOD.TOTL.GD.ZS": {"name": "Central government debt (% of GDP)", "name_cn": "政府债务占GDP比"},
}


class WorldBankProvider(BaseDataSource):
    """世界银行宏观数据源"""

    name = "Macro/WorldBank"
    BASE_URL = "https://api.worldbank.org/v2"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        self._limiter = RateLimiter(min_interval=0.5, jitter_min=0.2, jitter_max=0.8)

    def get_indicator(
        self,
        indicator_code: str,
        country: str = "all",
        date_range: Optional[str] = None,
        per_page: int = 50,
    ) -> Optional[Dict]:
        """
        获取世界银行指标数据

        Args:
            indicator_code: 指标代码，如 'NY.GDP.MKTP.CD'
            country: 国家代码或 'all'
            date_range: 日期范围，如 '2010:2024'
            per_page: 每页数量
        """
        self._limiter.wait()

        params = {
            "format": "json",
            "per_page": per_page,
        }
        if date_range:
            params["date"] = date_range

        url = f"{self.BASE_URL}/country/{country}/indicator/{indicator_code}"

        try:
            resp = self._session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if len(data) < 2:
                return None
            return {"pagination": data[0], "records": data[1]}
        except Exception as e:
            logger.error(f"[WorldBank] Request failed: {indicator_code} - {e}")
            return None

    def get_key_indicators(self, country: str = "all") -> Dict[str, Any]:
        """获取关键宏观指标最新值"""
        result = {}
        for code, meta in WB_KEY_INDICATORS.items():
            data = self.get_indicator(code, country=country, per_page=5)
            if data and data.get("records"):
                latest = data["records"][0]
                val = latest.get("value")
                result[code] = {
                    "name": meta["name"],
                    "name_cn": meta["name_cn"],
                    "value": float(val) if val else None,
                    "date": latest.get("date"),
                    "country": latest.get("country", {}).get("value", ""),
                    "country_code": latest.get("countryiso3code", ""),
                }
            else:
                result[code] = {"name": meta["name"], "name_cn": meta["name_cn"], "value": None}
        return result

    def get_country_list(self, income_level: Optional[str] = None) -> List[Dict]:
        """获取国家列表"""
        self._limiter.wait()
        params = {"format": "json", "per_page": 300}
        if income_level:
            params["incomeLevel"] = income_level

        try:
            resp = self._session.get(f"{self.BASE_URL}/country", params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if len(data) >= 2:
                return [
                    {
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "iso2": c.get("iso2Code"),
                        "region": c.get("region", {}).get("value", ""),
                        "income_level": c.get("incomeLevel", {}).get("value", ""),
                    }
                    for c in data[1] or []
                ]
        except Exception as e:
            logger.error(f"[WorldBank] Country list fetch failed: {e}")
        return []

    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        parts = symbol.upper().split(":")
        indicator_code = parts[0]
        country = parts[1] if len(parts) > 1 else "all"

        data = self.get_indicator(indicator_code, country=country, per_page=limit)
        if not data or not data.get("records"):
            return []

        klines = []
        for record in data.get("records", []):
            val = record.get("value")
            if not val:
                continue
            date_str = record.get("date", "")
            try:
                dt = datetime.strptime(date_str, "%Y")
                ts = int(dt.timestamp())
                fval = float(val)
                klines.append(self.format_kline(ts, fval, fval, fval, fval, 0))
            except (ValueError, TypeError):
                continue

        klines.sort(key=lambda x: x["time"])
        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        data = self.get_kline(symbol, "1Y", 1)
        if data:
            return {"last": data[-1]["close"], "symbol": symbol, "source": "WorldBank"}
        return {"last": 0, "symbol": symbol}
