"""
FMP (Financial Modeling Prep) 基本面数据源
FMP API - 财务报表、估值数据、财务比率
API文档: https://site.financialmodelingprep.com/developer/docs/
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


class FMPProvider(BaseDataSource):
    """FMP 基本面数据源"""

    name = "Fundamentals/FMP"
    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'QuantDinger/1.0'
        })
        # FMP 免费版 250次/天
        self._limiter = RateLimiter(min_interval=5.0, jitter_min=1.0, jitter_max=3.0)
        self._cache: Dict[str, Any] = {}

    def _resolve_api_key(self) -> str:
        """解析 API Key"""
        try:
            key = ConfigResolver.get_api_key("fundamentals_fmp", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("FMP_API_KEY", "").strip()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
        """发送请求到 FMP API"""
        if not self._api_key:
            logger.warning("[FMP] API key not configured")
            return None

        self._limiter.wait()

        url = f"{self.BASE_URL}/{endpoint}?apikey={self._api_key}"
        if params:
            for key, value in params.items():
                if value is not None:
                    url += f"&{key}={value}"

        try:
            resp = self._session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, dict):
                error = data.get("Error Message") or data.get("error")
                if error:
                    logger.warning(f"[FMP] API error: {error}")
                    return None

            return data
        except Exception as e:
            logger.error(f"[FMP] Request failed: {endpoint} - {e}")
            return None

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """获取实时报价"""
        data = self._make_request(f"quote/{symbol}")
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return {}

    def get_profile(self, symbol: str) -> Dict[str, Any]:
        """获取公司概况"""
        data = self._make_request(f"profile/{symbol}")
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return {}

    def get_income_statement(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """获取利润表"""
        params = {"period": period, "limit": limit}
        data = self._make_request(f"income-statement/{symbol}", params)
        if data and isinstance(data, list):
            return data
        return []

    def get_balance_sheet(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """获取资产负债表"""
        params = {"period": period, "limit": limit}
        data = self._make_request(f"balance-sheet-statement/{symbol}", params)
        if data and isinstance(data, list):
            return data
        return []

    def get_cash_flow(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """获取现金流量表"""
        params = {"period": period, "limit": limit}
        data = self._make_request(f"cash-flow-statement/{symbol}", params)
        if data and isinstance(data, list):
            return data
        return []

    def get_financial_ratios(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """获取财务比率"""
        params = {"period": period, "limit": limit}
        data = self._make_request(f"ratios/{symbol}", params)
        if data and isinstance(data, list):
            return data
        return []

    def get_key_metrics(
        self,
        symbol: str,
        period: str = "annual",
        limit: int = 5
    ) -> List[Dict]:
        """获取关键指标"""
        params = {"period": period, "limit": limit}
        data = self._make_request(f"key-metrics/{symbol}", params)
        if data and isinstance(data, list):
            return data
        return []

    def get_dcf(self, symbol: str) -> Optional[Dict]:
        """获取 DCF 估值"""
        data = self._make_request(f"discounted-cash-flow/{symbol}")
        if data and isinstance(data, list) and len(data) > 0:
            return data[0]
        return None

    def get_all_financials(self, symbol: str, period: str = "annual") -> Dict[str, Any]:
        """获取完整财务数据"""
        return {
            "income_statement": self.get_income_statement(symbol, period),
            "balance_sheet": self.get_balance_sheet(symbol, period),
            "cash_flow": self.get_cash_flow(symbol, period),
            "ratios": self.get_financial_ratios(symbol, period),
            "key_metrics": self.get_key_metrics(symbol, period),
            "dcf": self.get_dcf(symbol),
        }

    def get_key_indicators(self, symbol: str = "AAPL", limit: int = 10) -> Dict[str, Any]:
        """获取关键财务指标"""
        cache_key = f"fmp_indicators:{symbol}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached.get("_ts", 0) < 3600:
                return cached

        result = {}
        ratios = self.get_financial_ratios(symbol, limit=1)
        metrics = self.get_key_metrics(symbol, limit=1)

        if ratios:
            r = ratios[0]
            result = {
                "pe_ratio": r.get("priceEarningsRatio"),
                "pb_ratio": r.get("priceToBookRatio"),
                "roe": r.get("returnOnEquity"),
                "debt_to_equity": r.get("debtToEquity"),
                "current_ratio": r.get("currentRatio"),
            }

        if metrics:
            m = metrics[0]
            result.update({
                "market_cap": m.get("marketCap"),
                "revenue": m.get("revenuePerShare"),
                "eps": m.get("earningsPerShare"),
                "book_value": m.get("bookValuePerShare"),
            })

        result["_ts"] = time.time()
        self._cache[cache_key] = result
        return result

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """FMP 不直接提供 K线，主要用于基本面数据"""
        return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取实时报价"""
        data = self.get_quote(symbol.upper())
        if data:
            return {
                "last": data.get("price", 0),
                "symbol": symbol.upper(),
                "change": data.get("changesPercentage", 0),
                "source": "FMP",
            }
        return {"last": 0, "symbol": symbol}