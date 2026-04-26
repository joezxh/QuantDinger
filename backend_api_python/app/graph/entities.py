"""QuantDinger-specific Graphiti entity models.

These Pydantic models define the domain entities used when populating
and querying the knowledge graph. They are registered with Graphiti at
runtime via the adapter layer.
"""
from typing import Optional

from pydantic import Field


try:
    from graphiti_core.nodes import Entity
except ImportError:
    # Fallback if graphiti_core is not yet available
    Entity = object  # type: ignore[misc,assignment]


class StockCompany(Entity):  # type: ignore[misc,valid-type]
    """Stock market company entity."""

    ticker: str = Field(..., description="股票代码")
    name: str = Field(..., description="公司名称")
    industry: Optional[str] = Field(None, description="行业")
    market_cap: Optional[float] = Field(None, description="市值")


class CryptoAsset(Entity):  # type: ignore[misc,valid-type]
    """Cryptocurrency asset entity."""

    symbol: str = Field(..., description="交易对符号")
    chain: Optional[str] = Field(None, description="公链")
    category: Optional[str] = Field(None, description="类别")


class PolymarketEvent(Entity):  # type: ignore[misc,valid-type]
    """Polymarket prediction market event entity."""

    market_id: str = Field(..., description="市场ID")
    question: str = Field(..., description="预测问题")
    category: Optional[str] = Field(None, description="分类")


class Institution(Entity):  # type: ignore[misc,valid-type]
    """Financial institution or fund entity."""

    name: str = Field(..., description="机构名称")
    type: Optional[str] = Field(None, description="机构类型")


class KOL(Entity):  # type: ignore[misc,valid-type]
    """Key Opinion Leader entity (crypto Twitter/analyst)."""

    handle: str = Field(..., description="社交媒体账号")
    platform: Optional[str] = Field(None, description="平台")
    follower_count: Optional[int] = Field(None, description="粉丝数")
