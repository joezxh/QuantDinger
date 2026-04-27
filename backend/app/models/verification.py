"""Verification codes and OAuth links SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class VerificationCode(Base):
    __tablename__ = "sys_verification_codes"
    __table_args__ = (
        Index("idx_verification_codes_email", "email"),
        Index("idx_verification_codes_type", "type"),
        Index("idx_verification_codes_expires", "expires_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OAuthLink(Base):
    __tablename__ = "sys_oauth_links"
    __table_args__ = (
        Index("idx_oauth_links_user_id", "user_id"),
        Index("idx_oauth_links_provider", "provider"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    provider_email: Mapped[Optional[str]] = mapped_column(String(100))
    provider_name: Mapped[Optional[str]] = mapped_column(String(100))
    provider_avatar: Mapped[Optional[str]] = mapped_column(String(255))
    access_token: Mapped[Optional[str]] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[Optional[User]] = relationship("User", back_populates="oauth_links", lazy="selectin")
