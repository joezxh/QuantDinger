"""
CFTC (Commodity Futures Trading Commission) 期货持仓数据源
提供COT (Commitment of Traders) 报告，包含大商、投机、套保持仓
数据: https://publicreporting.cftc.gov/
"""
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


CFTC_COMMODITY_MAP = {
    "BTC": "BITCOIN - CHICAGO MERCANTILE EXCHANGE",
    "ETH": "ETHER - CHICAGO MERCANTILE EXCHANGE",
    "GOLD": "GOLD - COMMODITY EXCHANGE INC.",
    "SILVER": "SILVER - COMMODITY EXCHANGE INC.",
    "CRUDE_OIL": "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE EXCHANGE",
    "NATURAL_GAS": "NATURAL GAS - NEW YORK MERCANTILE EXCHANGE",
    "S_P_500": "S&P 500 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
    "NASDAQ_100": "NASDAQ-100 STOCK INDEX - CHICAGO MERCANTILE EXCHANGE",
    "US_TREASURY_BOND": "U.S. TREASURY BONDS - CHICAGO BOARD OF TRADE",
    "EURO_FX": "EURO FX - CHICAGO MERCANTILE EXCHANGE",
    "JPY": "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
}


class CFTCProvider(BaseDataSource):
    """CFTC 期货持仓数据源"""

    name = "Futures/CFTC"
    BASE_URL = "https://publicreporting.cftc.gov/resource/tqk6-3h35.json"

    def __init__(self):
        self._session = requests.Session()
        self._limiter = RateLimiter(min_interval=1.0, jitter_min=0.5, jitter_max=1.5)

    def _request(self, params: Dict) -> Optional[List[Dict]]:
        self._limiter.wait()
        try:
            resp = self._session.get(self.BASE_URL, params=params, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[CFTC] Request failed: {e}")
            return None

    def get_cot_report(
        self,
        commodity_key: str,
        limit: int = 52,
    ) -> List[Dict]:
        """
        获取COT报告数据

        Args:
            commodity_key: 商品键名，如 'BTC', 'GOLD', 'S_P_500'
            limit: 返回周数
        """
        commodity_name = CFTC_COMMODITY_MAP.get(commodity_key.upper())
        if not commodity_name:
            logger.warning(f"[CFTC] Unknown commodity: {commodity_key}")
            return []

        params = {
            "commodity": commodity_name,
            "$limit": limit,
            "$order": "report_date DESC",
        }

        data = self._request(params)
        if not data:
            return []

        result = []
        for row in data:
            try:
                result.append({
                    "commodity": commodity_key,
                    "report_date": row.get("report_date"),
                    "open_interest": int(row.get("open_interest", 0) or 0),
                    "dealer_long": int(row.get("dealer_positions_long_all", 0) or 0),
                    "dealer_short": int(row.get("dealer_positions_short_all", 0) or 0),
                    "asset_mgr_long": int(row.get("asset_mgr_positions_long_all", 0) or 0),
                    "asset_mgr_short": int(row.get("asset_mgr_positions_short_all", 0) or 0),
                    "lev_money_long": int(row.get("lev_money_positions_long_all", 0) or 0),
                    "lev_money_short": int(row.get("lev_money_positions_short_all", 0) or 0),
                    "noncomm_long": int(row.get("noncomm_positions_long_all", 0) or 0),
                    "noncomm_short": int(row.get("noncomm_positions_short_all", 0) or 0),
                    "comm_long": int(row.get("comm_positions_long_all", 0) or 0),
                    "comm_short": int(row.get("comm_positions_short_all", 0) or 0),
                })
            except (ValueError, TypeError):
                continue

        return result

    def get_latest_cot(self, commodity_key: str) -> Optional[Dict]:
        """获取最新COT报告"""
        reports = self.get_cot_report(commodity_key, limit=1)
        return reports[0] if reports else None

    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        reports = self.get_cot_report(symbol.upper(), limit=limit)
        if not reports:
            return []

        klines = []
        for report in reversed(reports):
            date_str = report.get("report_date", "")
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
                except ValueError:
                    continue

            ts_val = int(dt.timestamp())
            oi = report.get("open_interest", 0)
            klines.append(self.format_kline(ts_val, oi, oi, oi, oi, 0))

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        report = self.get_latest_cot(symbol.upper())
        if report:
            return {
                "last": report.get("open_interest", 0),
                "symbol": symbol,
                "date": report.get("report_date"),
                "source": "CFTC",
            }
        return {"last": 0, "symbol": symbol}
