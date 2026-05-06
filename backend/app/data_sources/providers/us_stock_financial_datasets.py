"""
Financial Datasets API 美股专业级数据源
提供结构化财务报表、内部交易、分析师预估、SEC文件等
API文档: https://docs.financialdatasets.ai/
"""
import os
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.config_resolver import ConfigResolver
from app.data_sources.rate_limiter import RateLimiter
from app.data_sources.cache_manager import DataCache
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FinancialDatasetsProvider(BaseDataSource):
    """Financial Datasets API 美股专业级数据源"""

    name = "USStock/FinancialDatasets"
    BASE_URL = "https://api.financialdatasets.ai"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
        })
        if self._api_key:
            self._session.headers.update({"x-api-key": self._api_key})
        self._limiter = RateLimiter(min_interval=0.5, jitter_min=0.2, jitter_max=0.8)
        self._cache = DataCache(name="financial_datasets", default_ttl=3600, max_size=200)

    def _resolve_api_key(self) -> str:
        try:
            key = ConfigResolver.get_api_key("us_stock_financial_datasets", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("FINANCIAL_DATASETS_API_KEY", "").strip()

    def _request(self, endpoint: str, params: Optional[Dict] = None, cache_ttl: Optional[int] = None) -> Optional[Dict]:
        cache_key = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        if cache_ttl is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        self._limiter.wait()

        try:
            resp = self._session.get(f"{self.BASE_URL}{endpoint}", params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            if cache_ttl is not None:
                self._cache.set(cache_key, data, ttl=cache_ttl)
            return data
        except Exception as e:
            logger.error(f"[FinancialDatasets] Request failed: {endpoint} - {e}")
            return None

    def get_income_statements(self, ticker: str, period: str = "annual", limit: int = 4) -> Optional[List[Dict]]:
        """获取利润表"""
        data = self._request("/financials/income-statements/", {"ticker": ticker, "period": period, "limit": limit}, cache_ttl=86400)
        if data:
            return data.get("income_statements")
        return None

    def get_balance_sheets(self, ticker: str, period: str = "annual", limit: int = 4) -> Optional[List[Dict]]:
        """获取资产负债表"""
        data = self._request("/financials/balance-sheets/", {"ticker": ticker, "period": period, "limit": limit}, cache_ttl=86400)
        if data:
            return data.get("balance_sheets")
        return None

    def get_cash_flow_statements(self, ticker: str, period: str = "annual", limit: int = 4) -> Optional[List[Dict]]:
        """获取现金流量表"""
        data = self._request("/financials/cash-flow-statements/", {"ticker": ticker, "period": period, "limit": limit}, cache_ttl=86400)
        if data:
            return data.get("cash_flow_statements")
        return None

    def get_all_financials(self, ticker: str, period: str = "annual", limit: int = 4) -> Optional[Dict]:
        """获取全部三表"""
        data = self._request("/financials/", {"ticker": ticker, "period": period, "limit": limit}, cache_ttl=86400)
        if data:
            return data.get("financials")
        return None

    def get_key_ratios(self, ticker: str) -> Optional[Dict]:
        """获取关键财务比率快照"""
        data = self._request("/financial-metrics/snapshot/", {"ticker": ticker}, cache_ttl=3600)
        if data:
            return data.get("snapshot")
        return None

    def get_insider_trades(self, ticker: str, limit: int = 10) -> Optional[List[Dict]]:
        """获取内部交易"""
        data = self._request("/insider-trades/", {"ticker": ticker, "limit": limit}, cache_ttl=3600)
        if data:
            return data.get("insider_trades")
        return None

    def get_analyst_estimates(self, ticker: str, period: str = "annual") -> Optional[List[Dict]]:
        """获取分析师预估"""
        data = self._request("/analyst-estimates/", {"ticker": ticker, "period": period}, cache_ttl=21600)
        if data:
            return data.get("analyst_estimates")
        return None

    def get_filings(self, ticker: str, filing_type: Optional[List[str]] = None, limit: int = 10) -> Optional[List[Dict]]:
        """获取SEC文件元数据"""
        params = {"ticker": ticker, "limit": limit}
        if filing_type:
            params["filing_type"] = filing_type
        data = self._request("/filings/", params)
        if data:
            return data.get("filings")
        return None

    def get_filing_items(self, ticker: str, filing_type: str, accession_number: str, items: Optional[List[str]] = None) -> Optional[Dict]:
        """获取SEC文件内容"""
        params = {"ticker": ticker, "filing_type": filing_type, "accession_number": accession_number}
        if items:
            params["item"] = items
        data = self._request("/filings/items/", params, cache_ttl=86400)
        return data

    def get_news(self, ticker: Optional[str] = None, limit: int = 5) -> Optional[List[Dict]]:
        """获取新闻"""
        params = {"limit": min(limit, 10)}
        if ticker:
            params["ticker"] = ticker.strip().upper()
        data = self._request("/news", params, cache_ttl=900)
        if data:
            return data.get("news")
        return None

    def get_segmented_revenues(self, ticker: str, period: str = "annual", limit: int = 4) -> Optional[Dict]:
        """获取分部营收"""
        data = self._request("/financials/segmented-revenues/", {"ticker": ticker, "period": period, "limit": limit}, cache_ttl=86400)
        if data:
            return data.get("segmented_revenues")
        return None

    def get_stock_prices(self, ticker: str, start_date: str, end_date: str, interval: str = "day") -> Optional[List[Dict]]:
        """获取历史股价"""
        data = self._request("/prices/", {
            "ticker": ticker, "interval": interval,
            "start_date": start_date, "end_date": end_date,
        })
        if data:
            return data.get("prices")
        return None

    def get_stock_price_snapshot(self, ticker: str) -> Optional[Dict]:
        """获取股价快照"""
        data = self._request("/prices/snapshot/", {"ticker": ticker})
        if data:
            return data.get("snapshot")
        return None

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        interval_map = {"1m": "minute", "5m": "minute", "15m": "minute", "1H": "minute", "1D": "day", "1W": "week"}
        interval = interval_map.get(timeframe, "day")

        from datetime import timedelta
        end_dt = datetime.now()
        if before_time:
            end_dt = datetime.fromtimestamp(before_time)

        days_map = {"1m": 3, "5m": 5, "15m": 10, "1H": 20, "1D": min(limit * 2, 3650), "1W": min(limit * 7, 3650)}
        days = days_map.get(timeframe, 365)
        start_dt = end_dt - timedelta(days=days)

        prices = self.get_stock_prices(
            symbol.upper(), start_date=start_dt.strftime("%Y-%m-%d"),
            end_date=end_dt.strftime("%Y-%m-%d"), interval=interval,
        )
        if not prices:
            return []

        klines = []
        for p in prices:
            try:
                dt = datetime.strptime(p.get("time", ""), "%Y-%m-%dT%H:%M:%S.%fZ")
                ts_val = int(dt.timestamp())
                klines.append(self.format_kline(
                    ts_val,
                    float(p.get("open", 0)),
                    float(p.get("high", 0)),
                    float(p.get("low", 0)),
                    float(p.get("close", 0)),
                    float(p.get("volume", 0)),
                ))
            except (ValueError, TypeError):
                continue

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        snapshot = self.get_stock_price_snapshot(symbol.upper())
        if snapshot:
            return {
                "last": snapshot.get("current_price") or snapshot.get("close"),
                "open": snapshot.get("open"),
                "high": snapshot.get("high"),
                "low": snapshot.get("low"),
                "volume": snapshot.get("volume"),
                "market_cap": snapshot.get("market_cap"),
                "symbol": symbol,
                "source": "FinancialDatasets",
            }
        return {"last": 0, "symbol": symbol}
