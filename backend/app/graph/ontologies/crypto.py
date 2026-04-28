"""Cryptocurrency market ontology — entities for on-chain and DeFi domain."""
from typing import Optional

from pydantic import Field

try:
    from graphiti_core.nodes import Entity
except ImportError:
    Entity = object  # type: ignore[misc,assignment]


class CryptoAsset(Entity):  # type: ignore[misc,valid-type]
    """Cryptocurrency token or trading pair."""

    symbol: str = Field(..., description="代币符号或交易对,如 BTC/USDT")
    name: Optional[str] = Field(None, description="资产名称")
    consensus: Optional[str] = Field(None, description="共识机制(PoW/PoS等)")
    chain: Optional[str] = Field(None, description="所属公链")
    market: str = Field(default="Crypto", description="市场分类")


class Protocol(Entity):  # type: ignore[misc,valid-type]
    """DeFi protocol, DApp, or on-chain service."""

    name: str = Field(..., description="协议名称")
    category: Optional[str] = Field(None, description="类别(DEX/Lending/Yield/Bridge)")
    chain: Optional[str] = Field(None, description="部署链")
    tvl_billion: Optional[float] = Field(None, description="TVL(十亿美元)")


class CryptoAccount(Entity):  # type: ignore[misc,valid-type]
    """On-chain wallet or social-media KOL account."""

    address: Optional[str] = Field(None, description="钱包地址")
    handle: Optional[str] = Field(None, description="社交媒体账号")
    platform: Optional[str] = Field(None, description="平台(Twitter/Discord等)")
    followers: Optional[int] = Field(None, description="粉丝数")
    label: Optional[str] = Field(None, description="标签(whale/kol/cex/cold_wallet)")
