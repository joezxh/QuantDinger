"""LLM load-balancing SQLAlchemy models (provider, api_key, model, call_log)."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, Text, Index, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LLmProvider(Base):
    __tablename__ = "sys_llm_provider"
    __table_args__ = (
        Index("idx_llm_provider_code", "code", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(256))
    api_type: Mapped[str] = mapped_column(String(32), default="openai")
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LLmApiKey(Base):
    __tablename__ = "sys_llm_api_key"
    __table_args__ = (
        Index("idx_qd_llm_api_key_provider", "provider_id"),
        Index("idx_qd_llm_api_key_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_llm_provider.id"), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(64))
    api_key_enc: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    weight: Mapped[int] = mapped_column(Integer, default=1)
    owner_id: Mapped[int] = mapped_column(BigInteger, default=0)
    is_public: Mapped[int] = mapped_column(SmallInteger, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LLmModel(Base):
    __tablename__ = "sys_llm_model"
    __table_args__ = (
        Index("idx_qd_llm_model_provider", "provider_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_llm_provider.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(64))
    lb_strategy: Mapped[str] = mapped_column(String(32), default="weighted_round_robin")
    retries: Mapped[int] = mapped_column(Integer, default=3)
    timeout: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LLmCallLog(Base):
    __tablename__ = "sys_llm_call_log"
    __table_args__ = (
        Index("idx_qd_llm_call_log_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_llm_api_key.id"), nullable=False)
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey("sys_llm_model.id"), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    status_code: Mapped[Optional[int]] = mapped_column(Integer)
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
