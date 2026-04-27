"""Notification and strategy log SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.strategy import StrategyTrading

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StrategyNotification(Base):
    __tablename__ = "trade_strategy_notifications"
    __table_args__ = (
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_strategy_id", "strategy_id"),
        Index("idx_notifications_is_read", "is_read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    strategy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trade_strategies_trading.id", ondelete="CASCADE"))
    symbol: Mapped[str] = mapped_column(String(50), default="")
    signal_type: Mapped[str] = mapped_column(String(30), default="")
    channels: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    message: Mapped[str] = mapped_column(Text, default="")
    payload_json: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship("User", back_populates="strategy_notifications", lazy="selectin")
    strategy: Mapped[Optional[StrategyTrading]] = relationship("StrategyTrading", back_populates="notifications", lazy="selectin")


class StrategyLog(Base):
    __tablename__ = "trade_strategy_logs"
    __table_args__ = (
        Index("idx_strategy_logs_strategy_id", "strategy_id"),
        Index("idx_strategy_logs_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(Integer, ForeignKey("trade_strategies_trading.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    strategy: Mapped[StrategyTrading] = relationship("StrategyTrading", back_populates="logs", lazy="selectin")
