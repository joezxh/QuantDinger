"""Polymarket prediction market ontology."""
from typing import Optional

from pydantic import Field

try:
    from graphiti_core.nodes import Entity
except ImportError:
    Entity = object  # type: ignore[misc,assignment]


class PredictionMarket(Entity):  # type: ignore[misc,valid-type]
    """Polymarket prediction market event."""

    market_id: str = Field(..., description="市场唯一ID")
    question: str = Field(..., description="预测问题")
    resolution_source: Optional[str] = Field(None, description="结算依据")
    category: Optional[str] = Field(None, description="分类")
    current_probability: Optional[float] = Field(None, description="当前概率(%)")
    active: bool = Field(default=True, description="是否活跃")


class MarketOutcome(Entity):  # type: ignore[misc,valid-type]
    """Individual outcome option within a prediction market."""

    outcome_id: str = Field(..., description="选项唯一ID")
    market_id: str = Field(..., description="所属市场ID")
    label: str = Field(..., description="选项标签(YES/NO/具体名称)")
    probability: Optional[float] = Field(None, description="当前概率")
