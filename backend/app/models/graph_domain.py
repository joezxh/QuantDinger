"""Domain-specific graph feature models."""
from datetime import date

from sqlalchemy import Date, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CompanyNarrativeFeature(Base, TimestampMixin):
    __tablename__ = "gra_company_narrative_features"
    __table_args__ = (
        UniqueConstraint("trade_date", "ticker", "narrative_name", name="uq_company_narrative_feature"),
        Index("idx_company_narrative_lookup", "ticker", "trade_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    narrative_name: Mapped[str] = mapped_column(String(100), nullable=False)
    narrative_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="graph")


class CryptoNarrativeFeature(Base, TimestampMixin):
    __tablename__ = "gra_crypto_narrative_features"
    __table_args__ = (
        UniqueConstraint("trade_date", "symbol", "narrative_name", name="uq_crypto_narrative_feature"),
        Index("idx_crypto_narrative_lookup", "symbol", "trade_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    narrative_name: Mapped[str] = mapped_column(String(100), nullable=False)
    narrative_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="graph")


class PolymarketMarketFeature(Base, TimestampMixin):
    __tablename__ = "gra_polymarket_market_features"
    __table_args__ = (
        UniqueConstraint("trade_date", "market_id", "feature_name", name="uq_polymarket_market_feature"),
        Index("idx_polymarket_feature_lookup", "market_id", "trade_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    market_id: Mapped[str] = mapped_column(String(255), nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_value: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="graph")
