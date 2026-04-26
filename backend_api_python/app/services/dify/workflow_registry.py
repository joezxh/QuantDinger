"""Workflow registry — resolves workflow codes to configuration records."""
from __future__ import annotations

from app.database.session import get_session
from app.database.repositories.dify_workflow_repository import DifyWorkflowRepository
from app.models.dify import DifyWorkflow
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowRegistry:
    """In-memory + DB backed registry for Dify workflow lookup by code."""

    def get_by_code(self, code: str) -> DifyWorkflow | None:
        """Fetch a workflow configuration by its unique code."""
        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                return repo.get_by_code(code)
        except Exception as exc:
            logger.error(f"WorkflowRegistry lookup failed for code={code}: {exc}")
            return None

    def list_active(self) -> list[DifyWorkflow]:
        """Return all currently active workflows."""
        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                return repo.list_active()
        except Exception as exc:
            logger.error(f"WorkflowRegistry list_active failed: {exc}")
            return []

    def list_all(self) -> list[DifyWorkflow]:
        """Return all workflows (active and inactive)."""
        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                return repo.list_all()
        except Exception as exc:
            logger.error(f"WorkflowRegistry list_all failed: {exc}")
            return []
