"""Indicator community full SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric,
    String, Text, Index, UniqueConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class IndicatorCode(Base):
    __tablename__ = "ind_indicator_codes"
    __table_args__ = (
        Index("idx_indicator_codes_user_id", "user_id"),
        Index("idx_indicator_review_status", "review_status"),
        Index("idx_indicator_codes_source", "source_indicator_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    is_buy: Mapped[int] = mapped_column(Integer, default=0)
    end_time: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(255), default="")
    code: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    publish_to_community: Mapped[int] = mapped_column(Integer, default=0)
    pricing_type: Mapped[str] = mapped_column(String(20), default="free")
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    is_encrypted: Mapped[int] = mapped_column(Integer, default=0)
    preview_image: Mapped[Optional[str]] = mapped_column(String(500))
    vip_free: Mapped[bool] = mapped_column(Boolean, default=False)
    createtime: Mapped[Optional[int]] = mapped_column(Integer)
    updatetime: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    purchase_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    review_status: Mapped[str] = mapped_column(String(20), default="approved")
    review_note: Mapped[str] = mapped_column(Text, default="")
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[Optional[int]] = mapped_column(Integer)
    source_indicator_id: Mapped[Optional[int]] = mapped_column(Integer)

    user: Mapped[User] = relationship("User", back_populates="indicator_codes", lazy="selectin")


class IndicatorPurchase(Base):
    __tablename__ = "ind_indicator_purchases"
    __table_args__ = (
        UniqueConstraint("indicator_id", "buyer_id"),
        Index("idx_purchases_indicator", "indicator_id"),
        Index("idx_purchases_buyer", "buyer_id"),
        Index("idx_purchases_seller", "seller_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[int] = mapped_column(Integer, ForeignKey("ind_indicator_codes.id", ondelete="CASCADE"), nullable=False)
    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False)
    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IndicatorComment(Base):
    __tablename__ = "ind_indicator_comments"
    __table_args__ = (
        Index("idx_comments_indicator", "indicator_id"),
        Index("idx_comments_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[int] = mapped_column(Integer, ForeignKey("ind_indicator_codes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, CheckConstraint("rating >= 1 AND rating <= 5"), default=5)
    content: Mapped[str] = mapped_column(Text, default="")
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ind_indicator_comments.id", ondelete="CASCADE"))
    is_deleted: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
