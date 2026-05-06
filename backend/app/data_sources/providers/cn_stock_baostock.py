"""
BaoStock A股数据源
免费A股数据接口，提供稳定的历史行情、财务数据
API文档: http://baostock.com/baostock/index.php/Python_API%E6%96%87%E6%A1%A3
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)

_BAOSTOCK_AVAILABLE = False
try:
    import baostock as bs
    _BAOSTOCK_AVAILABLE = True
except ImportError:
    pass


class BaoStockProvider(BaseDataSource):
    """BaoStock A股数据源"""

    name = "CNStock/BaoStock"

    FREQUENCY_MAP = {
        "1m": "5",     # BaoStock不提供1分钟，降级到5分钟
        "5m": "5",
        "15m": "15",
        "30m": "30",
        "1H": "60",
        "1D": "d",
        "1W": "w",
    }

    def __init__(self):
        self._connected = False
        self._limiter = RateLimiter(min_interval=0.5, jitter_min=0.3, jitter_max=1.0)

    def _ensure_connected(self) -> bool:
        if not _BAOSTOCK_AVAILABLE:
            return False
        if self._connected:
            return True
        try:
            lg = bs.login()
            if lg.error_code == "0":
                self._connected = True
                return True
            logger.error(f"[BaoStock] Login failed: {lg.error_msg}")
        except Exception as e:
            logger.error(f"[BaoStock] Connection failed: {e}")
        return False

    def _normalize_code(self, symbol: str) -> str:
        """标准化BaoStock股票代码格式: sh.600000 / sz.000001"""
        symbol = symbol.strip().lower()
        if "." in symbol:
            return symbol

        code = symbol.replace("sh", "").replace("sz", "").replace("bj", "")
        if code.startswith("6") or code.startswith("9"):
            return f"sh.{code}"
        return f"sz.{code}"

    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        if not self._ensure_connected():
            return []

        code = self._normalize_code(symbol)
        frequency = self.FREQUENCY_MAP.get(timeframe, "d")

        start_date = "1990-01-01"
        end_date = datetime.now().strftime("%Y-%m-%d")

        if before_time:
            end_date = datetime.fromtimestamp(before_time).strftime("%Y-%m-%d")

        self._limiter.wait()

        try:
            rs = bs.query_history_k_data_plus(
                code,
                "date,time,open,high,low,close,volume",
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag="3",
            )

            if rs.error_code != "0":
                logger.error(f"[BaoStock] Query failed: {rs.error_msg}")
                return []

            rows = []
            while (rs.error_code == "0") and rs.next():
                row = rs.get_row_data()
                if row:
                    rows.append(row)

            if not rows:
                return []

            klines = []
            for row in rows:
                try:
                    date_str = row[0]
                    if len(row) > 1 and row[1] and row[1] != "":
                        dt_str = f"{date_str} {row[1]}"
                        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M%S")
                    else:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")

                    ts_val = int(dt.timestamp())
                    klines.append(self.format_kline(
                        ts_val,
                        float(row[2] or 0),
                        float(row[3] or 0),
                        float(row[4] or 0),
                        float(row[5] or 0),
                        float(row[6] or 0),
                    ))
                except (ValueError, TypeError, IndexError):
                    continue

            return self.filter_and_limit(klines, limit, before_time)

        except Exception as e:
            logger.error(f"[BaoStock] get_kline failed: {code} - {e}")
            return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        klines = self.get_kline(symbol, "1D", 2)
        if klines:
            latest = klines[-1]
            prev = klines[-2] if len(klines) > 1 else latest
            change = latest["close"] - prev["close"]
            change_pct = (change / prev["close"] * 100) if prev["close"] else 0
            return {
                "last": latest["close"],
                "open": latest["open"],
                "high": latest["high"],
                "low": latest["low"],
                "volume": latest["volume"],
                "change": change,
                "changePercent": change_pct,
                "symbol": symbol,
                "source": "BaoStock",
            }
        return {"last": 0, "symbol": symbol}

    def __del__(self):
        if self._connected and _BAOSTOCK_AVAILABLE:
            try:
                bs.logout()
            except Exception:
                pass
