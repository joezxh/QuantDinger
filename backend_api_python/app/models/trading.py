"""Trading-related SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.strategy import StrategyTrading
    from app.models.user import User

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TradeOrder(Base, TimestampMixin):
    __tablename__ = "trade_trade_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    strategy_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[str] = mapped_column(String(20), nullable=False)
    order_type: Mapped[Optional[str]] = mapped_column(String(30))
    quantity: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
    price: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
    status: Mapped[Optional[str]] = mapped_column(String(30))
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[Optional[str]] = mapped_column(Text)


class StrategyTrade(Base):
    __tablename__ = "trade_strategy_trades"
    __table_args__ = (
        Index("idx_trades_user_id", "user_id"),
        Index("idx_trades_strategy_id", "strategy_id"),
        Index("idx_trades_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    strategy_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("trade_strategies_trading.id", ondelete="CASCADE"))
    symbol: Mapped[Optional[str]] = mapped_column(String(50))
    type: Mapped[Optional[str]] = mapped_column(String(30))
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 8))
    commission: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    commission_ccy: Mapped[str] = mapped_column(String(20), default="")
    profit: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship("User", back_populates="strategy_trades", lazy="selectin")
    strategy: Mapped[Optional[StrategyTrading]] = relationship("StrategyTrading", back_populates="trades", lazy="selectin")
