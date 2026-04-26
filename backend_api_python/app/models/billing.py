"""Billing-related SQLAlchemy models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class BillingRecord(Base, TimestampMixin):
    __tablename__ = "sys_billing_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    feature: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    balance_before: Mapped[Optional[float]] = mapped_column(Numeric(18, 4))
    balance_after: Mapped[Optional[float]] = mapped_column(Numeric(18, 4))
    reference_id: Mapped[Optional[str]] = mapped_column(String(100))
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[Optional[str]] = mapped_column(Text)
    billing_type: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[Optional[str]] = mapped_column(String(30))
