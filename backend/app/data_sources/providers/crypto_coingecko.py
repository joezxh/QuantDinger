"""
CoinGecko 加密货币数据源
免费聚合数据，提供市值排行、价格、DeFi TVL 等
API文档: https://www.coingecko.com/en/api/documentation
"""
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CoinGeckoProvider(BaseDataSource):
    """CoinGecko 加密货币数据源"""

    name = "Crypto/CoinGecko"
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
        })
        self._limiter = RateLimiter(min_interval=1.5, jitter_min=0.5, jitter_max=2.0)
        self._id_map: Dict[str, str] = {}

    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Any]:
        self._limiter.wait()
        try:
            resp = self._session.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=15)
            if resp.status_code == 429:
                logger.warning("[CoinGecko] Rate limited, backing off")
                time.sleep(60)
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[CoinGecko] Request failed: {endpoint} - {e}")
            return None

    def _resolve_coin_id(self, symbol: str) -> str:
        """将交易对符号解析为CoinGecko ID"""
        base = symbol.split("/")[0].split(":")[0].lower().strip()
        id_map = {
            "btc": "bitcoin", "eth": "ethereum", "sol": "solana",
            "xrp": "ripple", "ada": "cardano", "doge": "dogecoin",
            "dot": "polkadot", "matic": "matic-network", "avax": "avalanche-2",
            "link": "chainlink", "uni": "uniswap", "atom": "cosmos",
            "ltc": "litecoin", "bch": "bitcoin-cash", "near": "near",
            "apt": "aptos", "arb": "arbitrum", "op": "optimism",
            "shib": "shiba-inu", "pepe": "pepe", "wif": "dogwifcoin",
        }
        return id_map.get(base, base)

    def get_market_data(
        self,
        ids: Optional[str] = None,
        vs_currency: str = "usd",
        per_page: int = 100,
        page: int = 1,
        order: str = "market_cap_desc",
    ) -> List[Dict]:
        """获取市场数据（价格、市值、24h变化等）"""
        params = {
            "vs_currency": vs_currency,
            "order": order,
            "per_page": per_page,
            "page": page,
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d",
        }
        if ids:
            params["ids"] = ids

        data = self._request("coins/markets", params)
        if not data:
            return []

        return [
            {
                "id": c.get("id"),
                "symbol": c.get("symbol", "").upper(),
                "name": c.get("name"),
                "current_price": c.get("current_price"),
                "market_cap": c.get("market_cap"),
                "total_volume": c.get("total_volume"),
                "price_change_24h": c.get("price_change_percentage_24h"),
                "price_change_7d": c.get("price_change_percentage_7d_in_currency"),
                "high_24h": c.get("high_24h"),
                "low_24h": c.get("low_24h"),
                "ath": c.get("ath"),
                "ath_date": c.get("ath_date"),
                "circulating_supply": c.get("circulating_supply"),
                "total_supply": c.get("total_supply"),
            }
            for c in data
        ]

    def get_coin_detail(self, coin_id: str) -> Optional[Dict]:
        """获取币种详情"""
        data = self._request(f"coins/{coin_id}", {"localization": "false", "tickers": "false"})
        if not data:
            return None

        return {
            "id": data.get("id"),
            "symbol": data.get("symbol", "").upper(),
            "name": data.get("name"),
            "market_cap_rank": data.get("market_cap_rank"),
            "current_price": data.get("market_data", {}).get("current_price", {}).get("usd"),
            "total_value_locked": data.get("market_data", {}).get("total_value_locked", {}).get("usd"),
            "description": (data.get("description", {}).get("en") or "")[:500],
            "categories": data.get("categories", []),
        }

    def get_trending(self) -> List[Dict]:
        """获取热门币种"""
        data = self._request("search/trending")
        if not data:
            return []

        return [
            {
                "id": c.get("item", {}).get("id"),
                "symbol": c.get("item", {}).get("symbol", "").upper(),
                "name": c.get("item", {}).get("name"),
                "market_cap_rank": c.get("item", {}).get("market_cap_rank"),
                "price_btc": c.get("item", {}).get("price_btc"),
            }
            for c in data.get("coins", [])
        ]

    def get_global_data(self) -> Optional[Dict]:
        """获取全球加密市场概况"""
        data = self._request("global")
        if not data:
            return None

        gd = data.get("data", {})
        return {
            "total_market_cap_usd": gd.get("total_market_cap", {}).get("usd"),
            "total_volume_usd": gd.get("total_volume", {}).get("usd"),
            "btc_dominance": gd.get("market_cap_percentage", {}).get("btc"),
            "eth_dominance": gd.get("market_cap_percentage", {}).get("eth"),
            "active_cryptocurrencies": gd.get("active_cryptocurrencies"),
            "market_cap_change_24h_pct": gd.get("market_cap_change_percentage_24h_usd"),
        }

    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        coin_id = self._resolve_coin_id(symbol)

        days_map = {"1m": 1, "5m": 1, "15m": 1, "30m": 1, "1H": 1, "4H": 1, "1D": 90, "1W": 365}
        days = days_map.get(timeframe, 90)

        data = self._request(f"coins/{coin_id}/ohlc", {"vs_currency": "usd", "days": days})
        if not data:
            return []

        klines = []
        for entry in data:
            try:
                ts_val = int(entry[0] / 1000)
                klines.append(self.format_kline(
                    ts_val, float(entry[1]), float(entry[2]),
                    float(entry[3]), float(entry[4]), 0
                ))
            except (ValueError, TypeError, IndexError):
                continue

        return self.filter_and_limit(klines, limit, before_time)

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        coin_id = self._resolve_coin_id(symbol)
        data = self._request("simple/price", {"ids": coin_id, "vs_currencies": "usd", "include_24hr_change": "true"})
        if data and data.get(coin_id):
            info = data[coin_id]
            return {
                "last": info.get("usd"),
                "changePercent": info.get("usd_24h_change"),
                "symbol": symbol,
                "source": "CoinGecko",
            }
        return {"last": 0, "symbol": symbol}
