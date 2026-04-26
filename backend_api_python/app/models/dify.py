"""SQLAlchemy models for Dify workflow integration."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class DifyWorkflow(Base):
    """Registered Dify workflow configurations."""

    __tablename__ = "data_dify_workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    workflow_type: Mapped[str] = mapped_column(
        String(50), default="chat"
    )  # chat / workflow / completion
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), nullable=False)
    input_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    output_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=120)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )

    # Relationships
    logs: Mapped[list["DifyWorkflowLog"]] = relationship(
        "DifyWorkflowLog", back_populates="workflow", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<DifyWorkflow(id={self.id}, code={self.code})>"


class DifyWorkflowLog(Base):
    """Execution logs for Dify workflow calls."""

    __tablename__ = "data_dify_workflow_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(
        ForeignKey("data_dify_workflows.id"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_users.id"), nullable=True
    )
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending / running / success / failed
    call_mode: Mapped[str] = mapped_column(
        String(10), default="batch"
    )  # streaming / batch
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())

    # Relationships
    workflow: Mapped["DifyWorkflow"] = relationship(
        "DifyWorkflow", back_populates="logs"
    )
    user: Mapped["User | None"] = relationship("User", lazy="joined")

    def __repr__(self) -> str:
        return f"<DifyWorkflowLog(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"
