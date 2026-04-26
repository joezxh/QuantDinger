"""Exchange credential SQLAlchemy model."""
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ExchangeCredential(Base):
    __tablename__ = "trade_exchange_credentials"
    __table_args__ = (
        Index("idx_exchange_credentials_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_users.id", ondelete="CASCADE"), default=1)
    name: Mapped[str] = mapped_column(String(100), default="")
    exchange_id: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key_hint: Mapped[str] = mapped_column(String(50), default="")
    encrypted_config: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship("User", back_populates="exchange_credentials", lazy="selectin")
