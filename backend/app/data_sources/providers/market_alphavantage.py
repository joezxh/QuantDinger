"""
Alpha Vantage 市场数据源
Alpha Vantage API - 技术指标、情绪数据、外汇
API文档: https://www.alphavantage.co/documentation/
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


class AlphaVantageProvider(BaseDataSource):
    """Alpha Vantage 市场数据源"""

    name = "Market/AlphaVantage"
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self._api_key = self._resolve_api_key()
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'QuantDinger/1.0'
        })
        # Alpha Vantage 免费版 500次/天, 5次/分钟
        self._limiter = RateLimiter(min_interval=12.0, jitter_min=2.0, jitter_max=5.0)
        self._cache: Dict[str, Any] = {}

    def _resolve_api_key(self) -> str:
        """解析 API Key"""
        try:
            key = ConfigResolver.get_api_key("market_alphavantage", key_type="public")
            if key:
                return key
        except Exception:
            pass
        return os.getenv("ALPHA_VANTAGE_API_KEY", "").strip()

    def _make_request(self, params: Dict) -> Optional[Dict]:
        """发送请求到 Alpha Vantage API"""
        if not self._api_key:
            logger.warning("[AlphaVantage] API key not configured")
            return None

        self._limiter.wait()

        params["apikey"] = self._api_key

        try:
            resp = self._session.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # 检查错误
            if "Error Message" in data:
                logger.warning(f"[AlphaVantage] API error: {data['Error Message']}")
                return None
            if "Note" in data:
                logger.warning(f"[AlphaVantage] Rate limit: {data['Note']}")
                return None

            return data
        except Exception as e:
            logger.error(f"[AlphaVantage] Request failed: {e}")
            return None

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """获取实时报价 (GLOBAL_QUOTE)"""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol.upper()
        }
        data = self._make_request(params)
        if data and "Global Quote" in data:
            return data["Global Quote"]
        return {}

    def get_intraday(self, symbol: str, interval: str = "5min", output_size: str = "compact") -> List[Dict]:
        """获取日内数据 (TIME_SERIES_INTRADAY)"""
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol.upper(),
            "interval": interval,
            "outputsize": output_size
        }
        data = self._make_request(params)
        if not data:
            return []

        # 解析时间序列
        key = f"Time Series ({interval})"
        if key not in data:
            return []

        result = []
        for date_str, values in data[key].items():
            dt = datetime.fromisoformat(date_str.replace(" ", "T"))
            result.append({
                "time": int(dt.timestamp()),
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "volume": float(values.get("5. volume", 0)),
                "date": date_str,
            })
        return result

    def get_daily(self, symbol: str, output_size: str = "compact") -> List[Dict]:
        """获取日线数据 (TIME_SERIES_DAILY)"""
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol.upper(),
            "outputsize": output_size
        }
        data = self._make_request(params)
        if not data:
            return []

        key = "Time Series (Daily)"
        if key not in data:
            return []

        result = []
        for date_str, values in data[key].items():
            dt = datetime.fromisoformat(date_str)
            result.append({
                "time": int(dt.timestamp()),
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "volume": float(values.get("5. volume", 0)),
                "date": date_str,
            })
        return result

    def get_technical_indicator(
        self,
        symbol: str,
        indicator: str = "RSI",
        interval: str = "daily",
        time_period: int = 14,
        series_type: str = "close"
    ) -> List[Dict]:
        """获取技术指标 (RSI, MACD, BBANDS 等)"""
        params = {
            "function": indicator,
            "symbol": symbol.upper(),
            "interval": interval,
            "time_period": time_period,
            "series_type": series_type
        }
        data = self._make_request(params)
        if not data:
            return []

        # 找到数据键
        data_key = None
        for key in data.keys():
            if key.startswith("Technical Analysis"):
                data_key = key
                break

        if not data_key:
            return []

        result = []
        for date_str, values in data[data_key].items():
            dt = datetime.fromisoformat(date_str)
            item = {"time": int(dt.timestamp()), "date": date_str}
            for k, v in values.items():
                item[k.split(". ")[1]] = float(v)
            result.append(item)

        return result

    def get_fx_rate(self, from_currency: str, to_currency: str = "USD") -> Dict[str, Any]:
        """获取汇率 (CURRENCY_EXCHANGE_RATE)"""
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper()
        }
        data = self._make_request(params)
        if data and "Realtime Currency Exchange Rate" in data:
            rate_data = data["Realtime Currency Exchange Rate"]
            return {
                "from": rate_data.get("1. From_Currency Code"),
                "to": rate_data.get("3. To_Currency Code"),
                "rate": float(rate_data.get("5. Exchange Rate", 0)),
                "timestamp": rate_data.get("6. Last Refreshed"),
            }
        return {}

    def get_key_indicators(self, symbol: str = "IBM", limit: int = 5) -> Dict[str, Any]:
        """获取关键指标"""
        quote = self.get_quote(symbol)
        if not quote:
            return {}

        return {
            "symbol": quote.get("01. symbol"),
            "price": quote.get("05. price"),
            "change": quote.get("09. change"),
            "change_percent": quote.get("10. change percent"),
            "volume": quote.get("06. volume"),
            "high": quote.get("03. high"),
            "low": quote.get("04. low"),
            "latest_day": quote.get("07. latest trading day"),
        }

    # BaseDataSource interface
    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        """获取 K线数据"""
        # 转换 timeframe
        av_interval_map = {
            "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
            "1H": "60min", "4H": "60min", "1D": "daily", "1W": "daily"
        }
        interval = av_interval_map.get(timeframe, "daily")

        if interval in ["1min", "5min", "15min", "30min", "60min"]:
            data = self.get_intraday(symbol, interval)
        else:
            data = self.get_daily(symbol)

        klines = []
        for item in data:
            klines.append(self.format_kline(
                item["time"],
                item["open"],
                item["high"],
                item["low"],
                item["close"],
                item["volume"]
            ))

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取实时报价"""
        quote = self.get_quote(symbol)
        if quote:
            return {
                "last": float(quote.get("05. price", 0)),
                "symbol": quote.get("01. symbol", symbol),
                "change": quote.get("09. change", 0),
                "change_percent": quote.get("10. change percent", "0%"),
                "volume": int(quote.get("06. volume", 0)),
                "source": "AlphaVantage",
            }
        return {"last": 0, "symbol": symbol}