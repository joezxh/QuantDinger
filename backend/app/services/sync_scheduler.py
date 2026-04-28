"""
Generic sync task scheduler.
Supports registering different executors for various datasource types.
"""
import json
import os
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from app.database.session import get_session
from app.database.repositories.sync_repository import SyncRepository
from app.models.sync_task import SyncJob, SyncRun
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SyncTaskExecutor(ABC):
    """Abstract base class for datasource-specific sync executors."""

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the source type this executor handles (e.g., 'polymarket')."""
        ...

    @abstractmethod
    def execute(
        self,
        job: SyncJob,
        run: SyncRun,
        run_type: str = "incremental",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Execute the sync task.

        Args:
            job: The SyncJob configuration.
            run: The SyncRun record (already created with status='running').
            run_type: 'incremental' or 'full'.
            **kwargs: Extra parameters (e.g., limit for full sync).

        Returns:
            Dict with keys: status, items_fetched, items_saved, items_failed,
            error, detail, elapsed_sec
        """
        ...


class _JobWorker:
    """Internal per-job background worker thread."""

    def __init__(
        self,
        job: SyncJob,
        executor: SyncTaskExecutor,
        scheduler: "SyncScheduler",
    ):
        self.job_id = job.id
        self.job = job
        self.executor = executor
        self.scheduler = scheduler
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._last_update_ts = 0.0
        self._current_run_id: Optional[int] = None

    def start(self) -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return True
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                name=f"SyncWorker-{self.job_id}",
                daemon=True,
            )
            self._thread.start()
            logger.info(
                f"SyncWorker started for job {self.job_id} "
                f"(source={self.executor.source_type}, "
                f"interval={self.job.interval_minutes}min)"
            )
            return True

    def stop(self, timeout_sec: float = 5.0) -> None:
        with self._lock:
            if not self._thread or not self._thread.is_alive():
                return
            self._stop_event.set()
            self._thread.join(timeout=timeout_sec)
            if self._thread.is_alive():
                logger.warning(
                    f"SyncWorker-{self.job_id} did not stop within timeout"
                )
            else:
                logger.info(f"SyncWorker-{self.job_id} stopped")

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def trigger_now(self, run_type: str = "incremental", **kwargs: Any) -> None:
        """Trigger a manual run in a background thread."""
        t = threading.Thread(
            target=self._execute_once,
            args=(run_type,),
            kwargs=kwargs,
            name=f"SyncManual-{self.job_id}-{run_type}",
            daemon=True,
        )
        t.start()

    def _run_loop(self) -> None:
        logger.info(f"SyncWorker-{self.job_id} loop started")
        # Execute immediately on startup
        self._execute_once("incremental")

        while not self._stop_event.is_set():
            try:
                wait_seconds = self.job.interval_minutes * 60
                if self._stop_event.wait(wait_seconds):
                    break
                self._execute_once("incremental")
            except Exception as e:
                logger.error(
                    f"SyncWorker-{self.job_id} loop error: {e}", exc_info=True
                )
                self._stop_event.wait(60)

        logger.info(f"SyncWorker-{self.job_id} loop stopped")

    def _execute_once(self, run_type: str = "incremental", **kwargs: Any) -> None:
        """Execute one sync cycle with database record keeping."""
        from app.database.repositories.sync_repository import SyncRepository

        run_id = None
        try:
            with get_session() as session:
                repo = SyncRepository(session)
                fresh_job = repo.get_job(self.job_id)
                if fresh_job and not fresh_job.enabled:
                    logger.info(
                        f"Sync job {self.job_id} is disabled, skipping"
                    )
                    return

                run = repo.create_run(
                    job_id=self.job_id,
                    run_type=run_type,
                    status="running",
                )
                run_id = run.id
                self._current_run_id = run_id

            result = self.executor.execute(
                self.job, run, run_type=run_type, **kwargs
            )

            with get_session() as session:
                repo = SyncRepository(session)
                repo.update_run(
                    run_id=run_id,
                    status=result["status"],
                    finished_at=datetime.now(),
                    items_fetched=result.get("items_fetched"),
                    items_saved=result.get("items_saved"),
                    items_failed=result.get("items_failed"),
                    error_message=result.get("error"),
                    detail_json=json.dumps(result.get("detail", {})),
                )
                repo.update_job(
                    self.job_id,
                    last_run_at=datetime.now(),
                    next_run_at=datetime.now()
                    + timedelta(minutes=self.job.interval_minutes),
                    last_status=result["status"],
                    last_error=result.get("error"),
                )
                self._last_update_ts = time.time()

        except Exception as e:
            logger.error(
                f"Sync job {self.job_id} execution failed: {e}", exc_info=True
            )
            if run_id:
                try:
                    with get_session() as session:
                        repo = SyncRepository(session)
                        repo.update_run(
                            run_id=run_id,
                            status="failed",
                            finished_at=datetime.now(),
                            error_message=str(e),
                        )
                except Exception:
                    pass
        finally:
            self._current_run_id = None

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.is_running(),
            "job_id": self.job_id,
            "source_type": self.executor.source_type,
            "interval_minutes": self.job.interval_minutes,
            "last_update_ts": self._last_update_ts,
            "current_run_id": self._current_run_id,
        }


class SyncScheduler:
    """Central scheduler managing multiple sync job workers."""

    def __init__(self):
        self._executors: Dict[str, SyncTaskExecutor] = {}
        self._workers: Dict[int, _JobWorker] = {}
        self._lock = threading.Lock()

    def register_executor(self, executor: SyncTaskExecutor) -> None:
        """Register a datasource-specific executor."""
        self._executors[executor.source_type] = executor
        logger.info(f"Registered sync executor: {executor.source_type}")

    def start_job(self, job: SyncJob) -> bool:
        """Start a background worker for the given job."""
        executor = self._executors.get(job.executor_type or job.source_type)
        if executor is None:
            logger.error(
                f"No executor registered for source_type="
                f"{job.source_type}, executor_type={job.executor_type}"
            )
            return False

        with self._lock:
            if job.id in self._workers:
                self._workers[job.id].stop()
            worker = _JobWorker(job, executor, self)
            self._workers[job.id] = worker
            return worker.start()

    def stop_job(self, job_id: int) -> None:
        """Stop a specific job worker."""
        with self._lock:
            worker = self._workers.pop(job_id, None)
            if worker:
                worker.stop()

    def stop_all(self) -> None:
        """Stop all job workers."""
        with self._lock:
            for worker in self._workers.values():
                worker.stop()
            self._workers.clear()

    def trigger_job(self, job_id: int, run_type: str = "incremental", **kwargs: Any) -> bool:
        """Manually trigger a job execution."""
        with self._lock:
            worker = self._workers.get(job_id)
            if worker is None:
                # Try to start a temporary worker if job exists
                with get_session() as session:
                    repo = SyncRepository(session)
                    job = repo.get_job(job_id)
                if job is None:
                    return False
                executor = self._executors.get(job.executor_type or job.source_type)
                if executor is None:
                    return False
                worker = _JobWorker(job, executor, self)
                worker.trigger_now(run_type, **kwargs)
                return True
            worker.trigger_now(run_type, **kwargs)
            return True

    def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Get status of a specific job worker."""
        with self._lock:
            worker = self._workers.get(job_id)
            if worker:
                return worker.get_status()
        return None

    def get_all_status(self) -> List[Dict[str, Any]]:
        """Get status of all job workers."""
        with self._lock:
            return [w.get_status() for w in self._workers.values()]


# Global singleton
_scheduler: Optional[SyncScheduler] = None
_scheduler_lock = threading.Lock()


def get_sync_scheduler() -> SyncScheduler:
    """Get the global SyncScheduler singleton."""
    global _scheduler
    with _scheduler_lock:
        if _scheduler is None:
            _scheduler = SyncScheduler()
        return _scheduler
