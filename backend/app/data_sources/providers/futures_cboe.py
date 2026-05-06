# -*- coding: utf-8 -*-
"""
CBOE (Chicago Board Options Exchange) 波动率数据源
提供 VIX、VIX3M、VVIX、SKEW 等波动率指数历史数据
基于 CBOE 公开 CDN CSV 端点，无需 API Key
API文档: https://cdn.cboe.com/api/global/us_indices/daily_prices/
"""
import io
import csv
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)

# CBOE 公开 CDN 端点（无需 API Key）
CBOE_CDN_BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices"

# 支持的波动率指数及对应 CSV 文件名
CBOE_INDICES = {
    "VIX": {"file": "VIX_History.csv", "name": "CBOE Volatility Index", "name_cn": "VIX波动率指数"},
    "VIX3M": {"file": "VIX3M_History.csv", "name": "3-Month VIX", "name_cn": "3个月VIX"},
    "VVIX": {"file": "VVIX_History.csv", "name": "VVIX Index", "name_cn": "VIX的波动率指数"},
    "SKEW": {"file": "SKEW_History.csv", "name": "CBOE SKEW Index", "name_cn": "偏度指数"},
    "VXN": {"file": "VXN_History.csv", "name": "VXN Index", "name_cn": "纳斯达克100波动率"},
    "VXO": {"file": "VXO_History.csv", "name": "VXO Index", "name_cn": "S&P100波动率(旧)"},
    "GVZ": {"file": "GVZ_History.csv", "name": "Gold VIX", "name_cn": "黄金波动率"},
    "OVX": {"file": "OVX_History.csv", "name": "Oil VIX", "name_cn": "原油波动率"},
    "TYVIX": {"file": "TYVIX_History.csv", "name": "10Y Treasury VIX", "name_cn": "10年国债波动率"},
}

# VIX 期货期限结构端点
FUTURES_BASE = "https://cdn.cboe.com/api/global/futures/vx_eod_curve"


class CBOEProvider(BaseDataSource):
    """CBOE 波动率数据源（免费公开数据，无需 API Key）"""

    name = "Futures/CBOE"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "QuantDinger/1.0",
            "Accept": "text/csv,application/json",
        })
        self._limiter = RateLimiter(min_interval=1.0, jitter_min=0.3, jitter_max=0.8)
        self._cache: Dict[str, Any] = {}

    def _fetch_csv(self, filename: str) -> Optional[List[Dict[str, str]]]:
        """从 CBOE CDN 获取并解析 CSV"""
        url = f"{CBOE_CDN_BASE}/{filename}"
        self._limiter.wait()

        try:
            resp = self._session.get(url, timeout=20)
            resp.raise_for_status()
            reader = csv.DictReader(io.StringIO(resp.text))
            rows = []
            for row in reader:
                clean = {k.strip(): v.strip() for k, v in row.items() if k}
                if not any(clean.values()):
                    continue
                rows.append(clean)
            return rows
        except Exception as e:
            logger.error(f"[CBOE] CSV fetch failed for {filename}: {e}")
            return None

    def get_index_history(
        self,
        index_name: str = "VIX",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取波动率指数历史数据

        Args:
            index_name: 指数名称，如 'VIX', 'VIX3M', 'SKEW' 等
            start_date: 起始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD

        Returns:
            [{date, open, high, low, close}, ...]
        """
        name = index_name.upper()
        meta = CBOE_INDICES.get(name)
        if not meta:
            logger.warning(f"[CBOE] Unknown index: {index_name}")
            return []

        cache_key = f"cboe_{name}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.get("_ts", 0) < 3600:  # 1h cache
                rows = cached["data"]
            else:
                rows = self._fetch_csv(meta["file"])
                if rows is None:
                    rows = cached["data"]  # fallback to stale cache
                else:
                    self._cache[cache_key] = {"data": rows, "_ts": time.time()}
        else:
            rows = self._fetch_csv(meta["file"])
            if rows is None:
                return []
            self._cache[cache_key] = {"data": rows, "_ts": time.time()}

        result = []
        for row in rows:
            date_val = row.get("DATE", row.get("Date", ""))
            if start_date and date_val < start_date:
                continue
            if end_date and date_val > end_date:
                continue
            try:
                result.append({
                    "date": date_val,
                    "open": float(row.get("OPEN", row.get("Open", 0))),
                    "high": float(row.get("HIGH", row.get("High", 0))),
                    "low": float(row.get("LOW", row.get("Low", 0))),
                    "close": float(row.get("CLOSE", row.get("Close", 0))),
                })
            except (ValueError, TypeError):
                continue

        return result

    def get_vix_current(self) -> Dict[str, Any]:
        """获取 VIX 最新值"""
        history = self.get_index_history("VIX")
        if history:
            latest = history[-1]
            return {
                "last": latest["close"],
                "symbol": "VIX",
                "date": latest["date"],
                "open": latest["open"],
                "high": latest["high"],
                "low": latest["low"],
                "source": "CBOE",
            }
        return {"last": 0, "symbol": "VIX"}

    def get_available_indices(self) -> List[Dict[str, str]]:
        """获取可用指数列表"""
        return [
            {"symbol": k, "name": v["name"], "name_cn": v["name_cn"]}
            for k, v in CBOE_INDICES.items()
        ]

    def get_futures_term_structure(self, date: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """
        获取 VIX 期货期限结构

        Args:
            date: 日期 YYYY-MM-DD (None = 最新)

        Returns:
            [{symbol, expiration, price, ...}, ...]
        """
        if date:
            url = f"{FUTURES_BASE}/{date}.json"
        else:
            url = f"{FUTURES_BASE}.json"

        self._limiter.wait()
        try:
            resp = self._session.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            logger.error(f"[CBOE] Futures term structure fetch failed: {e}")
            return None

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """
        将 CBOE 指数历史数据转换为 K 线格式

        Args:
            symbol: 指数名称，如 'VIX', 'SKEW'
            timeframe: 仅支持日线 ('1D')
            limit: 数据条数
            before_time: Unix 时间戳（秒）
        """
        name = symbol.upper().replace("^", "")
        if name not in CBOE_INDICES:
            return []

        end_date = None
        if before_time:
            end_dt = datetime.fromtimestamp(before_time)
            end_date = end_dt.strftime("%Y-%m-%d")

        # 粗略估算起始日期（日线数据，多取一些余量）
        start_dt = datetime.now()
        start_date = start_dt.strftime("%Y-%m-%d")  # CBOE CSV 本身就是全部历史

        rows = self.get_index_history(name, end_date=end_date)
        if not rows:
            return []

        klines = []
        for row in rows:
            try:
                dt = datetime.strptime(row["date"], "%Y-%m-%d")
                ts = int(dt.timestamp())
                klines.append(self.format_kline(
                    ts, row["open"], row["high"], row["low"], row["close"], 0
                ))
            except (ValueError, TypeError):
                continue

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取指数最新值"""
        name = symbol.upper().replace("^", "")
        history = self.get_index_history(name)
        if history:
            latest = history[-1]
            return {
                "last": latest["close"],
                "symbol": symbol,
                "date": latest["date"],
                "source": "CBOE",
            }
        return {"last": 0, "symbol": symbol}
