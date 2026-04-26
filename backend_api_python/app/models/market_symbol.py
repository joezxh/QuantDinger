"""Market symbol SQLAlchemy model."""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MarketSymbol(Base):
    __tablename__ = "trade_market_symbols"
    __table_args__ = (
        UniqueConstraint("market", "symbol"),
        Index("idx_market_symbols_market", "market"),
        Index("idx_market_symbols_is_hot", "market", "is_hot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), default="")
    exchange: Mapped[str] = mapped_column(String(50), default="")
    currency: Mapped[str] = mapped_column(String(10), default="")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    is_hot: Mapped[int] = mapped_column(Integer, default=0)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
