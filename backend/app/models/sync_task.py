"""Generic sync task job models for multi-datasource scheduling."""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class SyncJob(Base, TimestampMixin):
    """Generic data sync job configuration."""
    __tablename__ = "trade_sync_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="Data Sync"
    )
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="polymarket"
    )
    executor_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="polymarket"
    )
    interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[Optional[str]] = mapped_column(String(32))
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    config_json: Mapped[Optional[str]] = mapped_column(Text)


class SyncRun(Base):
    """Generic data sync execution history."""
    __tablename__ = "trade_sync_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    run_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="incremental"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="running"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    items_fetched: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    items_saved: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    items_failed: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    detail_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
