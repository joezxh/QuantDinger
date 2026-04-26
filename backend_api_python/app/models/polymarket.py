"""Polymarket-related SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class PolymarketUser(Base, TimestampMixin):
    __tablename__ = "trade_polymarket_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    win_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    volume: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
    payload_json: Mapped[Optional[str]] = mapped_column(Text)


class PolymarketMarket(Base, TimestampMixin):
    __tablename__ = "trade_polymarket_markets"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    current_probability: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    end_date_iso: Mapped[Optional[str]] = mapped_column(String(64))
    active: Mapped[Optional[bool]] = mapped_column(default=True)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[Optional[str]] = mapped_column(Text)


class PolymarketAnalysis(Base):
    __tablename__ = "trade_polymarket_ai_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_predicted_probability: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    market_probability: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    divergence: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    recommendation: Mapped[Optional[str]] = mapped_column(String(32))
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    opportunity_score: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    key_factors: Mapped[Optional[dict]] = mapped_column(JSONB)
    related_assets: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PolymarketOpportunity(Base, TimestampMixin):
    __tablename__ = "trade_polymarket_opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    market_id: Mapped[str] = mapped_column(String(255), nullable=False)
    asset: Mapped[str] = mapped_column(String(100), nullable=False)
    market: Mapped[Optional[str]] = mapped_column(String(50))
    signal: Mapped[Optional[str]] = mapped_column(String(32))
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    reasoning: Mapped[Optional[str]] = mapped_column(Text)
    payload_json: Mapped[Optional[str]] = mapped_column(Text)
