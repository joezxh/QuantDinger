"""Credits log SQLAlchemy model."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class CreditsLog(Base):
    __tablename__ = "sys_credits_log"
    __table_args__ = (
        Index("idx_credits_log_user_id", "user_id"),
        Index("idx_credits_log_action", "action"),
        Index("idx_credits_log_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    feature: Mapped[str] = mapped_column(String(50), default="")
    reference_id: Mapped[str] = mapped_column(String(100), default="")
    remark: Mapped[Optional[str]] = mapped_column(Text)
    operator_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship("User", back_populates="credits_logs", lazy="selectin")
