"""Repository for Dify workflow configuration and execution logs."""
from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.models.dify import DifyWorkflow, DifyWorkflowLog


class DifyWorkflowRepository(BaseRepository):
    # ------------------------------------------------------------------
    # Workflow CRUD
    # ------------------------------------------------------------------
    def get_by_id(self, workflow_id: int) -> DifyWorkflow | None:
        return self.session.get(DifyWorkflow, workflow_id)

    def get_by_code(self, code: str) -> DifyWorkflow | None:
        stmt = select(DifyWorkflow).where(DifyWorkflow.code == code)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[DifyWorkflow]:
        stmt = select(DifyWorkflow).order_by(DifyWorkflow.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def list_active(self) -> list[DifyWorkflow]:
        stmt = select(DifyWorkflow).where(DifyWorkflow.is_active.is_(True))
        return list(self.session.execute(stmt).scalars().all())

    def create(self, **kwargs) -> DifyWorkflow:
        wf = DifyWorkflow(**kwargs)
        self.add(wf)
        self.flush()
        return wf

    def update_by_code(self, code: str, **kwargs) -> DifyWorkflow | None:
        wf = self.get_by_code(code)
        if not wf:
            return None
        for key, value in kwargs.items():
            if hasattr(wf, key):
                setattr(wf, key, value)
        self.flush()
        return wf

    def delete_by_code(self, code: str) -> bool:
        wf = self.get_by_code(code)
        if not wf:
            return False
        self.session.delete(wf)
        self.flush()
        return True

    # ------------------------------------------------------------------
    # Log CRUD
    # ------------------------------------------------------------------
    def create_log(self, **kwargs) -> DifyWorkflowLog:
        log = DifyWorkflowLog(**kwargs)
        self.add(log)
        self.flush()
        return log

    def get_logs_by_workflow(self, workflow_id: int, limit: int = 100) -> list[DifyWorkflowLog]:
        stmt = (
            select(DifyWorkflowLog)
            .where(DifyWorkflowLog.workflow_id == workflow_id)
            .order_by(DifyWorkflowLog.created_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())

    def update_log_status(self, log_id: int, status: str, **kwargs) -> DifyWorkflowLog | None:
        log = self.session.get(DifyWorkflowLog, log_id)
        if not log:
            return None
        log.status = status
        for key, value in kwargs.items():
            if hasattr(log, key):
                setattr(log, key, value)
        self.flush()
        return log
