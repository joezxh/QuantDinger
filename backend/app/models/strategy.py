"""Strategy-related SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.notification import StrategyLog, StrategyNotification
    from app.models.order import PendingOrder
    from app.models.position import StrategyPosition
    from app.models.trading import StrategyTrade
    from app.models.user import User

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Strategy(Base, TimestampMixin):
    __tablename__ = "trade_strategies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    strategy_type: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), default="draft")
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)


class StrategyTrading(Base, TimestampMixin):
    __tablename__ = "trade_strategies_trading"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    strategy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    strategy_type: Mapped[str] = mapped_column(String(50), default="IndicatorStrategy")
    market_category: Mapped[str] = mapped_column(String(50), default="Crypto")
    execution_mode: Mapped[str] = mapped_column(String(20), default="signal")
    notification_config: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="stopped")
    symbol: Mapped[Optional[str]] = mapped_column(String(50))
    timeframe: Mapped[Optional[str]] = mapped_column(String(10))
    initial_capital: Mapped[Decimal] = mapped_column(Numeric(20, 8), default=1000)
    leverage: Mapped[int] = mapped_column(Integer, default=1)
    market_type: Mapped[str] = mapped_column(String(20), default="swap")
    exchange_config: Mapped[Optional[str]] = mapped_column(Text)
    indicator_config: Mapped[Optional[str]] = mapped_column(Text)
    trading_config: Mapped[Optional[str]] = mapped_column(Text)
    ai_model_config: Mapped[Optional[str]] = mapped_column(Text)
    decide_interval: Mapped[int] = mapped_column(Integer, default=300)
    strategy_group_id: Mapped[str] = mapped_column(String(100), default="")
    group_base_name: Mapped[str] = mapped_column(String(255), default="")
    strategy_mode: Mapped[str] = mapped_column(String(20), default="signal")
    strategy_code: Mapped[str] = mapped_column(Text, default="")
    last_rebalance_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # Legacy column from old schema
    strategy_id: Mapped[Optional[int]] = mapped_column(default=None)

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="strategy_tradings", lazy="selectin")
    positions: Mapped[list[StrategyPosition]] = relationship("StrategyPosition", back_populates="strategy", lazy="selectin")
    pending_orders: Mapped[list[PendingOrder]] = relationship("PendingOrder", back_populates="strategy", lazy="selectin")
    notifications: Mapped[list[StrategyNotification]] = relationship("StrategyNotification", back_populates="strategy", lazy="selectin")
    trades: Mapped[list[StrategyTrade]] = relationship("StrategyTrade", back_populates="strategy", lazy="selectin")
    logs: Mapped[list[StrategyLog]] = relationship("StrategyLog", back_populates="strategy", lazy="selectin")
