"""Collection-related SQLAlchemy models."""
from typing import Optional

from sqlalchemy import String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CollectionRecord(Base, TimestampMixin):
    __tablename__ = "sys_collection_records"
    __table_args__ = (
        UniqueConstraint("content_hash", name="uq_collection_content_hash"),
        Index("idx_collection_lookup", "source", "data_type", "market", "symbol"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[Optional[str]] = mapped_column(String(50))
    data_type: Mapped[Optional[str]] = mapped_column(String(50))
    market: Mapped[Optional[str]] = mapped_column(String(50))
    symbol: Mapped[Optional[str]] = mapped_column(String(100))
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
