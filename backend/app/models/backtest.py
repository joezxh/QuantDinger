"""Backtest-related SQLAlchemy models."""
from typing import Optional

from sqlalchemy import Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class BacktestResult(Base, TimestampMixin):
    __tablename__ = "ind_backtest_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    strategy_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    run_type: Mapped[Optional[str]] = mapped_column(String(50))
    strategy_name: Mapped[Optional[str]] = mapped_column(String(255))
    engine_version: Mapped[Optional[str]] = mapped_column(String(50))
    code_hash: Mapped[Optional[str]] = mapped_column(String(128))
    config_snapshot: Mapped[Optional[str]] = mapped_column(Text)
    total_return: Mapped[Optional[float]] = mapped_column(Numeric(18, 6))
    win_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    max_drawdown: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    payload_json: Mapped[Optional[str]] = mapped_column(Text)


class BacktestTrade(Base, TimestampMixin):
    __tablename__ = "ind_backtest_trades"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    strategy_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    trade_index: Mapped[Optional[int]] = mapped_column(nullable=True)
    trade_time: Mapped[Optional[str]] = mapped_column(String(64))
    trade_type: Mapped[Optional[str]] = mapped_column(String(64))
    side: Mapped[Optional[str]] = mapped_column(String(32))
    price: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
    amount: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
    profit: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
    balance: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
    reason: Mapped[Optional[str]] = mapped_column(String(64))
    payload_json: Mapped[Optional[str]] = mapped_column(Text)


class BacktestEquityPoint(Base, TimestampMixin):
    __tablename__ = "ind_backtest_equity_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(nullable=False)
    point_index: Mapped[Optional[int]] = mapped_column(nullable=True)
    point_time: Mapped[Optional[str]] = mapped_column(String(64))
    point_value: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
