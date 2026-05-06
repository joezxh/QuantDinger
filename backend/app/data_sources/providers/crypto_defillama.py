"""
DeFi Llama 数据源
提供DeFi协议TVL、链级TVL、收益等数据
API文档: https://defillama.com/docs/api
"""
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import requests

from app.data_sources.base import BaseDataSource
from app.data_sources.rate_limiter import RateLimiter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DefiLlamaProvider(BaseDataSource):
    """DeFi Llama 数据源"""

    name = "Crypto/DeFiLlama"
    BASE_URL = "https://api.llama.fi"

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/json"})
        self._limiter = RateLimiter(min_interval=0.5, jitter_min=0.2, jitter_max=0.8)

    def _request(self, url: str, params: Optional[Dict] = None) -> Optional[Any]:
        self._limiter.wait()
        try:
            resp = self._session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"[DeFiLlama] Request failed: {url} - {e}")
            return None

    def get_protocols(self) -> List[Dict]:
        """获取所有DeFi协议列表及TVL"""
        data = self._request(f"{self.BASE_URL}/protocols")
        if not data:
            return []

        return [
            {
                "id": p.get("id") or p.get("slug"),
                "name": p.get("name"),
                "symbol": p.get("symbol", "").upper(),
                "tvl": p.get("tvl"),
                "chain": p.get("chain"),
                "category": p.get("category"),
                "change_1d": p.get("change_1d"),
                "change_7d": p.get("change_7d"),
                "mcap": p.get("mcap"),
                "fdv": p.get("fdv"),
            }
            for p in data
            if p.get("tvl") and p["tvl"] > 0
        ]

    def get_protocol_tvl(self, protocol_slug: str) -> Optional[Dict]:
        """获取单个协议详细TVL数据"""
        data = self._request(f"{self.BASE_URL}/protocol/{protocol_slug}")
        if not data:
            return None

        return {
            "name": data.get("name"),
            "symbol": data.get("symbol", "").upper(),
            "tvl": data.get("tvl"),
            "chain": data.get("chain"),
            "chains": data.get("chains", []),
            "category": data.get("category"),
            "current_chain_tvls": data.get("currentChainTvls", {}),
        }

    def get_chains_tvl(self) -> List[Dict]:
        """获取各链TVL"""
        data = self._request(f"{self.BASE_URL}/v2/chains")
        if not data:
            return []

        return [
            {
                "name": c.get("name"),
                "tvl": c.get("tvl"),
                "token_symbol": c.get("tokenSymbol"),
                "gecko_id": c.get("gecko_id"),
                "change_1d": c.get("change_1d"),
                "change_7d": c.get("change_7d"),
                "change_1m": c.get("change_1m"),
            }
            for c in data
            if c.get("tvl") and c["tvl"] > 0
        ]

    def get_global_tvl(self) -> Optional[Dict]:
        """获取全球DeFi TVL"""
        data = self._request(f"{self.BASE_URL}/overview/dexs")
        if data:
            return {
                "total_24h_volume": data.get("total24h"),
                "total_7d_volume": data.get("total7d"),
                "change_1d": data.get("change_1d"),
            }
        return None

    def get_dex_volumes(self) -> List[Dict]:
        """获取DEX交易量排行"""
        data = self._request(f"{self.BASE_URL}/overview/dexs")
        if not data or not data.get("protocols"):
            return []

        return [
            {
                "name": p.get("name"),
                "total_24h": p.get("total24h"),
                "total_7d": p.get("total7d"),
                "change_1d": p.get("change_1d"),
            }
            for p in data["protocols"][:50]
        ]

    def get_kline(self, symbol: str, timeframe: str, limit: int, before_time=None) -> List[Dict]:
        # DeFi Llama不提供传统K线数据，返回空列表
        return []

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        # DeFi Llama不提供实时报价
        return {"last": 0, "symbol": symbol}
