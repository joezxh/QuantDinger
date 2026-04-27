"""Market-related SQLAlchemy models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MarketPrice(Base, TimestampMixin):
    __tablename__ = "trade_market_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    change_percent: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    snapshot_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class MarketKline(Base, TimestampMixin):
    __tablename__ = "trade_market_klines"

    id: Mapped[int] = mapped_column(primary_key=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(100), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(20), nullable=False)
    open_price: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    high_price: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    low_price: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    close_price: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    volume: Mapped[Optional[float]] = mapped_column(Numeric(24, 8))
    kline_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[Optional[str]] = mapped_column(Text)
