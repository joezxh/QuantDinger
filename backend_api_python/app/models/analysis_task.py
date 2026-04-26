"""Analysis task and memory SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AnalysisTask(Base):
    __tablename__ = "analy_analysis_tasks"
    __table_args__ = (
        Index("idx_analysis_tasks_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), default="")
    language: Mapped[str] = mapped_column(String(20), default="en-US")
    status: Mapped[str] = mapped_column(String(20), default="completed")
    result_json: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship("User", back_populates="analysis_tasks", lazy="selectin")


class AnalysisMemory(Base):
    __tablename__ = "analy_analysis_memory"
    __table_args__ = (
        Index("idx_analysis_memory_symbol", "market", "symbol"),
        Index("idx_analysis_memory_created", "created_at"),
        Index("idx_analysis_memory_validated", "validated_at"),
        Index("idx_analysis_memory_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    decision: Mapped[str] = mapped_column(String(10), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, default=50)
    price_at_analysis: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8))
    summary: Mapped[Optional[str]] = mapped_column(Text)
    reasons: Mapped[Optional[dict]] = mapped_column(JSONB)
    scores: Mapped[Optional[dict]] = mapped_column(JSONB)
    indicators_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB)
    raw_result: Mapped[Optional[dict]] = mapped_column(JSONB)
    consensus_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8))
    consensus_abs: Mapped[Optional[Decimal]] = mapped_column(Numeric(24, 8))
    agreement_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    quality_multiplier: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_outcome: Mapped[Optional[str]] = mapped_column(String(20))
    actual_return_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4))
    was_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    user_feedback: Mapped[Optional[str]] = mapped_column(String(20))
    feedback_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
