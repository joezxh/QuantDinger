"""Workflow configuration manager — CRUD for qd_dify_workflows."""
from __future__ import annotations

from typing import Any, Dict

from app.database.session import get_session
from app.database.repositories.dify_workflow_repository import DifyWorkflowRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowManager:
    """High-level manager for Dify workflow configurations."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    def create(self, data: Dict[str, Any]) -> dict:
        """Register a new workflow."""
        required = {"code", "name", "endpoint", "api_key"}
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                # Check for duplicate code
                if repo.get_by_code(data["code"]):
                    raise ValueError(f"Workflow code already exists: {data['code']}")

                wf = repo.create(**data)
                session.commit()
                return self._to_dict(wf)
        except Exception as exc:
            logger.error(f"Workflow create failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get(self, code: str) -> dict | None:
        """Get a workflow by code."""
        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                wf = repo.get_by_code(code)
                return self._to_dict(wf) if wf else None
        except Exception as exc:
            logger.error(f"Workflow get failed: {exc}")
            raise

    def list_all(self) -> list[dict]:
        """List all workflows."""
        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                workflows = repo.list_all()
                return [self._to_dict(wf) for wf in workflows]
        except Exception as exc:
            logger.error(f"Workflow list failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, code: str, data: Dict[str, Any]) -> dict | None:
        """Update a workflow by code."""
        # Prevent changing the unique code
        data.pop("code", None)

        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                wf = repo.update_by_code(code, **data)
                if not wf:
                    return None
                session.commit()
                return self._to_dict(wf)
        except Exception as exc:
            logger.error(f"Workflow update failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------
    def delete(self, code: str) -> bool:
        """Delete a workflow by code."""
        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                ok = repo.delete_by_code(code)
                if ok:
                    session.commit()
                return ok
        except Exception as exc:
            logger.error(f"Workflow delete failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------
    @staticmethod
    def _to_dict(wf) -> dict:
        return {
            "id": wf.id,
            "code": wf.code,
            "name": wf.name,
            "description": wf.description,
            "workflow_type": wf.workflow_type,
            "endpoint": wf.endpoint,
            "api_key": "***",  # Mask sensitive value
            "input_schema": wf.input_schema,
            "output_schema": wf.output_schema,
            "is_active": wf.is_active,
            "max_retries": wf.max_retries,
            "timeout_seconds": wf.timeout_seconds,
            "created_at": wf.created_at.isoformat() if wf.created_at else None,
            "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
        }
