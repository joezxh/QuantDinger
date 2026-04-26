"""Order-related SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.strategy import StrategyTrading

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Integer, Numeric, String,
    Text, Index, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PendingOrder(Base):
    __tablename__ = "trade_pending_orders"
    __table_args__ = (
        Index("idx_pending_orders_user_id", "user_id"),
        Index("idx_pending_orders_status", "status"),
        Index("idx_pending_orders_strategy_id", "strategy_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    strategy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trade_strategies_trading.id", ondelete="SET NULL"))
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(30), nullable=False)
    signal_ts: Mapped[Optional[int]] = mapped_column(BigInteger)
    market_type: Mapped[str] = mapped_column(String(20), default="swap")
    order_type: Mapped[str] = mapped_column(String(20), default="market")
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    execution_mode: Mapped[str] = mapped_column(String(20), default="signal")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=10)
    last_error: Mapped[str] = mapped_column(Text, default="")
    payload_json: Mapped[str] = mapped_column(Text, default="")
    dispatch_note: Mapped[str] = mapped_column(Text, default="")
    exchange_id: Mapped[str] = mapped_column(String(50), default="")
    exchange_order_id: Mapped[str] = mapped_column(String(100), default="")
    exchange_response_json: Mapped[str] = mapped_column(Text, default="")
    filled: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship("User", back_populates="pending_orders", lazy="selectin")
    strategy: Mapped[Optional[StrategyTrading]] = relationship("StrategyTrading", back_populates="pending_orders", lazy="selectin")


class QuickTrade(Base):
    __tablename__ = "trade_quick_trades"
    __table_args__ = (
        Index("idx_quick_trades_user", "user_id"),
        Index("idx_quick_trades_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False)
    credential_id: Mapped[int] = mapped_column(Integer, default=0)
    exchange_id: Mapped[str] = mapped_column(String(40), default="")
    symbol: Mapped[str] = mapped_column(String(60), default="")
    side: Mapped[str] = mapped_column(String(10), default="")  # buy / sell
    order_type: Mapped[str] = mapped_column(String(20), default="market")  # market / limit
    amount: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    price: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    leverage: Mapped[int] = mapped_column(Integer, default=1)
    market_type: Mapped[str] = mapped_column(String(20), default="swap")  # swap / spot
    tp_price: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    sl_price: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    status: Mapped[str] = mapped_column(String(20), default="submitted")  # submitted / filled / failed / cancelled
    exchange_order_id: Mapped[str] = mapped_column(String(120), default="")
    filled_amount: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    avg_fill_price: Mapped[Decimal] = mapped_column(Numeric(24, 8), default=0)
    error_msg: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(40), default="manual")  # ai_radar / ai_analysis / indicator / manual
    raw_result: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship("User", back_populates="quick_trades", lazy="selectin")
