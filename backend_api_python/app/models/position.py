"""Position-related SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.strategy import StrategyTrading

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Integer, Numeric, String,
    Text, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StrategyPosition(Base):
    __tablename__ = "trade_strategy_positions"
    __table_args__ = (
        UniqueConstraint("strategy_id", "symbol", "side"),
        Index("idx_positions_user_id", "user_id"),
        Index("idx_positions_strategy_id", "strategy_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    strategy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trade_strategies_trading.id", ondelete="CASCADE"))
    symbol: Mapped[Optional[str]] = mapped_column(String(50))
    side: Mapped[Optional[str]] = mapped_column(String(10))  # long/short
    size: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    entry_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    current_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    highest_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    lowest_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    pnl_percent: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=0)
    equity: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship("User", back_populates="strategy_positions", lazy="selectin")
    strategy: Mapped[Optional[StrategyTrading]] = relationship("StrategyTrading", back_populates="positions", lazy="selectin")


class ManualPosition(Base):
    __tablename__ = "trade_manual_positions"
    __table_args__ = (
        UniqueConstraint("user_id", "market", "symbol", "side", "group_name"),
        Index("idx_manual_positions_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), default="")
    side: Mapped[str] = mapped_column(String(10), default="long")
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    entry_time: Mapped[Optional[int]] = mapped_column(BigInteger)
    notes: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(Text, default="")
    group_name: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship("User", back_populates="manual_positions", lazy="selectin")


class PositionAlert(Base):
    __tablename__ = "trade_position_alerts"
    __table_args__ = (
        Index("idx_position_alerts_user_id", "user_id"),
        Index("idx_position_alerts_position_id", "position_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    position_id: Mapped[Optional[int]] = mapped_column(Integer)
    market: Mapped[str] = mapped_column(String(50), default="")
    symbol: Mapped[str] = mapped_column(String(50), default="")
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    notification_config: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    is_triggered: Mapped[int] = mapped_column(Integer, default=0)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    repeat_interval: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship("User", back_populates="position_alerts", lazy="selectin")


class PositionMonitor(Base):
    __tablename__ = "trade_position_monitors"
    __table_args__ = (
        Index("idx_position_monitors_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    name: Mapped[str] = mapped_column(String(100), default="")
    position_ids: Mapped[str] = mapped_column(Text, default="")
    monitor_type: Mapped[str] = mapped_column(String(20), default="ai")
    config: Mapped[str] = mapped_column(Text, default="")
    notification_config: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_result: Mapped[str] = mapped_column(Text, default="")
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship("User", back_populates="position_monitors", lazy="selectin")
