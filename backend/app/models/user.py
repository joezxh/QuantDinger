"""User-related SQLAlchemy models."""
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.analysis_task import AnalysisTask
    from app.models.credits import CreditsLog
    from app.models.exchange import ExchangeCredential
    from app.models.indicator_full import IndicatorCode
    from app.models.membership import MembershipOrder, UsdtOrder
    from app.models.notification import StrategyNotification
    from app.models.order import PendingOrder, QuickTrade
    from app.models.permission import Role
    from app.models.position import ManualPosition, PositionAlert, PositionMonitor, StrategyPosition
    from app.models.strategy import StrategyTrading
    from app.models.trading import StrategyTrade
    from app.models.verification import OAuthLink
    from app.models.watchlist import Watchlist

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "sys_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(50))
    avatar: Mapped[Optional[str]] = mapped_column(String(255), default="/avatar2.jpg")
    status: Mapped[str] = mapped_column(String(20), default="active")
    role: Mapped[str] = mapped_column(String(20), default="user")
    credits: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0)
    vip_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    vip_plan: Mapped[str] = mapped_column(String(20), default="")
    vip_is_lifetime: Mapped[bool] = mapped_column(Boolean, default=False)
    vip_monthly_credits_last_grant: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    referred_by: Mapped[Optional[int]] = mapped_column(Integer)
    notification_settings: Mapped[str] = mapped_column(Text, default="")
    chart_templates: Mapped[str] = mapped_column(Text, default="")
    timezone: Mapped[Optional[str]] = mapped_column(String(64))
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    token_version: Mapped[int] = mapped_column(default=1)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    bio: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    credits_logs: Mapped[list[CreditsLog]] = relationship("CreditsLog", back_populates="user", lazy="selectin")
    membership_orders: Mapped[list[MembershipOrder]] = relationship("MembershipOrder", back_populates="user", lazy="selectin")
    usdt_orders: Mapped[list[UsdtOrder]] = relationship("UsdtOrder", back_populates="user", lazy="selectin")
    oauth_links: Mapped[list[OAuthLink]] = relationship("OAuthLink", back_populates="user", lazy="selectin")
    indicator_codes: Mapped[list[IndicatorCode]] = relationship("IndicatorCode", back_populates="user", lazy="selectin")
    watchlists: Mapped[list[Watchlist]] = relationship("Watchlist", back_populates="user", lazy="selectin")
    analysis_tasks: Mapped[list[AnalysisTask]] = relationship("AnalysisTask", back_populates="user", lazy="selectin")
    strategy_tradings: Mapped[list[StrategyTrading]] = relationship("StrategyTrading", back_populates="user", lazy="selectin")
    strategy_positions: Mapped[list[StrategyPosition]] = relationship("StrategyPosition", back_populates="user", lazy="selectin")
    manual_positions: Mapped[list[ManualPosition]] = relationship("ManualPosition", back_populates="user", lazy="selectin")
    position_alerts: Mapped[list[PositionAlert]] = relationship("PositionAlert", back_populates="user", lazy="selectin")
    position_monitors: Mapped[list[PositionMonitor]] = relationship("PositionMonitor", back_populates="user", lazy="selectin")
    pending_orders: Mapped[list[PendingOrder]] = relationship("PendingOrder", back_populates="user", lazy="selectin")
    quick_trades: Mapped[list[QuickTrade]] = relationship("QuickTrade", back_populates="user", lazy="selectin")
    exchange_credentials: Mapped[list[ExchangeCredential]] = relationship("ExchangeCredential", back_populates="user", lazy="selectin")
    strategy_trades: Mapped[list[StrategyTrade]] = relationship("StrategyTrade", back_populates="user", lazy="selectin")
    strategy_notifications: Mapped[list[StrategyNotification]] = relationship("StrategyNotification", back_populates="user", lazy="selectin")
    roles: Mapped[list[Role]] = relationship(
        "Role", secondary="sys_user_roles", back_populates="users", lazy="selectin"
    )
