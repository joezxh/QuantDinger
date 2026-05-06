"""
Tushare A股数据源
专业级A股数据接口，提供高质量的历史行情、财务数据、实时行情等
API文档: https://tushare.pro/document/2
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)

_TUSHARE_AVAILABLE = False
_ts = None

try:
    import tushare as ts
    _TUSHARE_AVAILABLE = True
except ImportError:
    pass


class TushareProvider(BaseDataSource):
    """Tushare A股数据源"""

    name = "CNStock/Tushare"

    TIMEFRAME_MAP = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "30m": "30min",
        "1H": "60min",
        "1D": "D",
        "1W": "W",
    }

    def __init__(self):
        self._api = None
        self._limiter = RateLimiter(min_interval=0.3, jitter_min=0.1, jitter_max=0.5)
        self._initialize()

    def _initialize(self):
        if not _TUSHARE_AVAILABLE:
            logger.warning("[Tushare] tushare library not installed")
            return

        token = self._resolve_token()
        if not token:
            logger.warning("[Tushare] No token configured")
            return

        try:
            ts.set_token(token)
            self._api = ts.pro_api()
            logger.info("[Tushare] Initialized successfully")
        except Exception as e:
            logger.error(f"[Tushare] Init failed: {e}")

    def _resolve_token(self) -> str:
        try:
            key = ConfigResolver.get_api_key("cn_stock_tushare", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("TUSHARE_TOKEN", "").strip()

    @property
    def available(self) -> bool:
        return self._api is not None

    def _normalize_ts_code(self, symbol: str) -> str:
        """标准化Tushare股票代码格式: 000001.SZ"""
        symbol = symbol.strip().upper()
        if "." in symbol:
            return symbol

        code = symbol.replace("SH", "").replace("SZ", "").replace("BJ", "")
        if symbol.endswith("SH") or code.startswith("6"):
            return f"{code}.SH"
        elif symbol.endswith("SZ") or code.startswith("0") or code.startswith("3"):
            return f"{code}.SZ"
        elif symbol.endswith("BJ") or code.startswith("8") or code.startswith("4"):
            return f"{code}.BJ"
        return f"{code}.SZ"

    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        if not self.available:
            return []

        ts_code = self._normalize_ts_code(symbol)
        freq = self.TIMEFRAME_MAP.get(timeframe, "D")

        self._limiter.wait()

        try:
            if freq == "D":
                df = self._api.daily(ts_code=ts_code, limit=limit)
            elif freq == "W":
                df = self._api.weekly(ts_code=ts_code, limit=limit)
            else:
                df = self._api.stk_mins(ts_code=ts_code, freq=freq, limit=limit)

            if df is None or df.empty:
                return []

            klines = []
            for _, row in df.iterrows():
                try:
                    if "trade_date" in row:
                        dt = datetime.strptime(str(row["trade_date"]), "%Y%m%d")
                    elif "trade_time" in row:
                        dt = datetime.strptime(str(row["trade_time"]), "%Y-%m-%d %H:%M:%S")
                    else:
                        continue

                    ts_val = int(dt.timestamp())
                    klines.append(self.format_kline(
                        ts_val,
                        float(row.get("open", 0) or 0),
                        float(row.get("high", 0) or 0),
                        float(row.get("low", 0) or 0),
                        float(row.get("close", 0) or 0),
                        float(row.get("vol", 0) or 0),
                    ))
                except (ValueError, TypeError):
                    continue

            return self.filter_and_limit(klines, limit, before_time)

        except Exception as e:
            logger.error(f"[Tushare] get_kline failed: {ts_code} - {e}")
            return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        if not self.available:
            return {"last": 0, "symbol": symbol}

        ts_code = self._normalize_ts_code(symbol)
        self._limiter.wait()

        try:
            df = self._api.daily(ts_code=ts_code, limit=1)
            if df is not None and not df.empty:
                row = df.iloc[0]
                close = float(row.get("close", 0) or 0)
                pre_close = float(row.get("pre_close", 0) or 0)
                change_pct = ((close - pre_close) / pre_close * 100) if pre_close else 0
                return {
                    "last": close,
                    "open": float(row.get("open", 0) or 0),
                    "high": float(row.get("high", 0) or 0),
                    "low": float(row.get("low", 0) or 0),
                    "volume": float(row.get("vol", 0) or 0),
                    "change": close - pre_close,
                    "changePercent": change_pct,
                    "symbol": symbol,
                    "source": "Tushare",
                }
        except Exception as e:
            logger.error(f"[Tushare] get_ticker failed: {ts_code} - {e}")

        return {"last": 0, "symbol": symbol}

    def get_financial(
        self,
        symbol: str,
        period: Optional[str] = None,
        report_type: str = "income",
    ) -> Optional[Any]:
        """获取财务数据"""
        if not self.available:
            return None

        ts_code = self._normalize_ts_code(symbol)
        self._limiter.wait()

        try:
            if report_type == "income":
                df = self._api.income(ts_code=ts_code, period=period)
            elif report_type == "balancesheet":
                df = self._api.balancesheet(ts_code=ts_code, period=period)
            elif report_type == "cashflow":
                df = self._api.cashflow(ts_code=ts_code, period=period)
            else:
                return None

            return df.to_dict("records") if df is not None and not df.empty else None
        except Exception as e:
            logger.error(f"[Tushare] get_financial failed: {ts_code} - {e}")
            return None
