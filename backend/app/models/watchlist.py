"""Watchlist SQLAlchemy model."""
from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Watchlist(Base):
    __tablename__ = "trade_watchlist"
    __table_args__ = (
        UniqueConstraint("user_id", "market", "symbol"),
        Index("idx_watchlist_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship("User", back_populates="watchlists", lazy="selectin")
