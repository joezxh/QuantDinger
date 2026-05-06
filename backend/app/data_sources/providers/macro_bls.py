"""
BLS (Bureau of Labor Statistics) 宏观数据源
美国劳工统计局，提供就业、CPI、薪资等数据
API文档: https://api.bls.gov/publicAPI/
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


BLS_KEY_SERIES = {
    "LNS14000000": {"name": "Unemployment Rate", "name_cn": "失业率", "unit": "%"},
    "CUSR0000SA0": {"name": "CPI All Items", "name_cn": "CPI(所有项目)", "unit": "Index"},
    "CUSR0000SA0L1E": {"name": "CPI Less Food & Energy", "name_cn": "核心CPI", "unit": "Index"},
    "CIU1010000000000I": {"name": "Hourly Earnings Growth", "name_cn": "时薪增长率", "unit": "%"},
    "LNS12300000": {"name": "Labor Force Participation Rate", "name_cn": "劳动参与率", "unit": "%"},
    "LNS11000000": {"name": "Employment Level", "name_cn": "就业人口", "unit": "Thousand"},
    "CES0000000001": {"name": "Total Nonfarm Employment", "name_cn": "非农就业", "unit": "Thousand"},
    "LNS13000000": {"name": "Unemployment Level", "name_cn": "失业人口", "unit": "Thousand"},
}


class BLSProvider(BaseDataSource):
    """BLS 宏观经济数据源"""

    name = "Macro/BLS"
    BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._limiter = RateLimiter(min_interval=1.0, jitter_min=0.5, jitter_max=1.5)

    def _resolve_api_key(self) -> str:
        try:
            key = ConfigResolver.get_api_key("macro_bls", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("BLS_API_KEY", "").strip()

    def get_series_data(
        self,
        series_ids: List[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        批量获取BLS时间序列数据

        Args:
            series_ids: 序列ID列表
            start_year: 起始年份
            end_year: 结束年份
        """
        current_year = datetime.now().year
        if not start_year:
            start_year = current_year - 1
        if not end_year:
            end_year = current_year

        self._limiter.wait()

        payload = {
            "seriesid": series_ids,
            "startyear": str(start_year),
            "endyear": str(end_year),
        }
        if self._api_key:
            payload["registrationKey"] = self._api_key

        try:
            resp = self._session.post(self.BASE_URL, json=payload, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[BLS] Request failed: {e}")
            return None

    def get_key_indicators(self) -> Dict[str, Any]:
        """获取关键宏观指标最新值"""
        series_ids = list(BLS_KEY_SERIES.keys())
        data = self.get_series_data(series_ids)
        result = {}

        if not data or data.get("status") != "REQUEST_SUCCEEDED":
            logger.warning(f"[BLS] API returned: {data.get('status', 'unknown') if data else 'no data'}")
            return result

        for series in data.get("Results", {}).get("series", []):
            sid = series.get("seriesID", "")
            meta = BLS_KEY_SERIES.get(sid, {})
            observations = series.get("data", [])

            if observations:
                latest = observations[0]
                val = latest.get("value")
                result[sid] = {
                    "name": meta.get("name", sid),
                    "name_cn": meta.get("name_cn", sid),
                    "value": float(val) if val else None,
                    "date": f"{latest.get('year')}-{latest.get('period', '').replace('M', '').zfill(2)}",
                    "period": latest.get("periodName", ""),
                    "unit": meta.get("unit", ""),
                }
            else:
                result[sid] = {
                    "name": meta.get("name", sid),
                    "name_cn": meta.get("name_cn", sid),
                    "value": None,
                    "date": None,
                }

        return result

    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        series_id = symbol.upper()
        if series_id not in BLS_KEY_SERIES:
            return []

        data = self.get_series_data([series_id])
        if not data:
            return []

        klines = []
        for series in data.get("Results", {}).get("series", []):
            for obs in series.get("data", []):
                val = obs.get("value")
                if not val:
                    continue
                year = obs.get("year")
                period = obs.get("period", "")
                month = period.replace("M", "").zfill(2)
                try:
                    dt = datetime.strptime(f"{year}-{month}", "%Y-%m")
                    ts = int(dt.timestamp())
                    fval = float(val)
                    klines.append(self.format_kline(ts, fval, fval, fval, fval, 0))
                except (ValueError, TypeError):
                    continue

        klines.sort(key=lambda x: x["time"])
        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        data = self.get_series_data([symbol.upper()])
        if data:
            for series in data.get("Results", {}).get("series", []):
                observations = series.get("data", [])
                if observations:
                    latest = observations[0]
                    val = latest.get("value")
                    return {
                        "last": float(val) if val else None,
                        "symbol": symbol,
                        "date": f"{latest.get('year')}-{latest.get('period', '').replace('M', '').zfill(2)}",
                        "source": "BLS",
                    }
        return {"last": 0, "symbol": symbol}
