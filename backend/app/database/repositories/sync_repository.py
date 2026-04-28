"""Generic sync task repository helpers."""
from typing import List, Optional

from sqlalchemy import desc, func, select

from app.database.repositories.base import BaseRepository
from app.models.sync_task import SyncJob, SyncRun


class SyncRepository(BaseRepository):
    # ------------------------------------------------------------------
    # Job CRUD
    # ------------------------------------------------------------------
    def get_job(self, job_id: int) -> Optional[SyncJob]:
        stmt = select(SyncJob).where(SyncJob.id == job_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_job_by_source(self, source_type: str) -> Optional[SyncJob]:
        stmt = (
            select(SyncJob)
            .where(SyncJob.source_type == source_type)
            .order_by(SyncJob.id)
        )
        return self.session.execute(stmt).scalars().first()

    def list_jobs(
        self,
        source_type: Optional[str] = None,
        executor_type: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[SyncJob]:
        stmt = select(SyncJob)
        if source_type is not None:
            stmt = stmt.where(SyncJob.source_type == source_type)
        if executor_type is not None:
            stmt = stmt.where(SyncJob.executor_type == executor_type)
        if enabled_only:
            stmt = stmt.where(SyncJob.enabled.is_(True))
        stmt = stmt.order_by(SyncJob.id)
        return list(self.session.execute(stmt).scalars().all())

    def create_job(self, **kwargs) -> SyncJob:
        job = SyncJob(**kwargs)
        self.add(job)
        self.flush()
        return job

    def update_job(self, job_id: int, **kwargs) -> Optional[SyncJob]:
        job = self.get_job(job_id)
        if job is None:
            return None
        for k, v in kwargs.items():
            if hasattr(job, k):
                setattr(job, k, v)
        self.flush()
        return job

    def delete_job(self, job_id: int) -> bool:
        job = self.get_job(job_id)
        if job is None:
            return False
        self.session.delete(job)
        self.flush()
        return True

    # ------------------------------------------------------------------
    # Run history
    # ------------------------------------------------------------------
    def create_run(self, **kwargs) -> SyncRun:
        run = SyncRun(**kwargs)
        self.add(run)
        self.flush()
        return run

    def get_run(self, run_id: int) -> Optional[SyncRun]:
        stmt = select(SyncRun).where(SyncRun.id == run_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_runs(
        self,
        job_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[SyncRun]:
        stmt = select(SyncRun)
        if job_id is not None:
            stmt = stmt.where(SyncRun.job_id == job_id)
        if status is not None:
            stmt = stmt.where(SyncRun.status == status)
        stmt = stmt.order_by(desc(SyncRun.id)).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def count_runs(
        self,
        job_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> int:
        stmt = select(func.count(SyncRun.id))
        if job_id is not None:
            stmt = stmt.where(SyncRun.job_id == job_id)
        if status is not None:
            stmt = stmt.where(SyncRun.status == status)
        return self.session.execute(stmt).scalar() or 0

    def update_run(self, run_id: int, **kwargs) -> Optional[SyncRun]:
        run = self.get_run(run_id)
        if run is None:
            return None
        for k, v in kwargs.items():
            if hasattr(run, k):
                setattr(run, k, v)
        self.flush()
        return run
