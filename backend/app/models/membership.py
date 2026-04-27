"""Membership and USDT order SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MembershipOrder(Base):
    __tablename__ = "sys_membership_orders"
    __table_args__ = (
        Index("idx_membership_orders_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[str] = mapped_column(String(20), default="paid")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship("User", back_populates="membership_orders", lazy="selectin")


class UsdtOrder(Base):
    __tablename__ = "sys_usdt_orders"
    __table_args__ = (
        Index("idx_usdt_orders_user_id", "user_id"),
        Index("idx_usdt_orders_status", "status"),
        Index("idx_usdt_orders_address_unique", "chain", "address", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)
    chain: Mapped[str] = mapped_column(String(20), default="TRC20")
    amount_usdt: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    address_index: Mapped[int] = mapped_column(Integer, default=0)
    address: Mapped[str] = mapped_column(String(80), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    tx_hash: Mapped[str] = mapped_column(String(120), default="")
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship("User", back_populates="usdt_orders", lazy="selectin")
