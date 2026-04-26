"""Graph-related SQLAlchemy models."""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Date, DateTime, Numeric, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class GraphEpisode(Base, TimestampMixin):
    __tablename__ = "gra_graph_episodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    episode_type: Mapped[str] = mapped_column(String(50), nullable=False)
    market_domain: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255))
    dedup_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    importance_score: Mapped[float] = mapped_column(Numeric(6, 4), default=0.5)
    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    observed_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text)


class GraphJob(Base, TimestampMixin):
    __tablename__ = "gra_graph_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    episode_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    retry_count: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class GraphEntityRef(Base, TimestampMixin):
    __tablename__ = "gra_graph_entity_refs"
    __table_args__ = (
        UniqueConstraint("entity_type", "source_table", "source_pk", name="uq_graph_entity_ref"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_table: Mapped[str] = mapped_column(String(100), nullable=False)
    source_pk: Mapped[str] = mapped_column(String(100), nullable=False)


class GraphRelationSnapshot(Base, TimestampMixin):
    __tablename__ = "gra_graph_relation_snapshots"
    __table_args__ = (
        Index("idx_graph_relation_lookup", "relation_type", "from_uid", "to_uid"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    relation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    from_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    to_uid: Mapped[str] = mapped_column(String(255), nullable=False)
    source_ref: Mapped[Optional[str]] = mapped_column(String(255))
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(6, 4))
    t_valid: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    t_invalid: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[Optional[str]] = mapped_column(Text)


class GraphFeatureDaily(Base, TimestampMixin):
    __tablename__ = "gra_graph_feature_daily"
    __table_args__ = (
        UniqueConstraint("trade_date", "market", "symbol", "feature_name", name="uq_graph_feature_daily"),
        Index("idx_graph_feature_lookup", "market", "symbol", "trade_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_name: Mapped[str] = mapped_column(String(100), nullable=False)
    feature_value: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="graph")
