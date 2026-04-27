"""Analysis-related SQLAlchemy models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AnalysisResult(Base, TimestampMixin):
    __tablename__ = "trade_analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[Optional[str]] = mapped_column(String(30))
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    payload_json: Mapped[Optional[str]] = mapped_column(Text)


class AiCalibration(Base):
    __tablename__ = "trade_ai_calibration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    buy_threshold: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    sell_threshold: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    min_consensus_abs_override: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    quality_hold_threshold: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
