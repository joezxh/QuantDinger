"""
Generic sync task scheduler management API routes.
Provides CRUD for sync jobs, manual trigger, run history and status monitoring.
"""
import threading

from flask import Blueprint, request, jsonify

from app.utils.auth import login_required, admin_required
from app.utils.logger import get_logger
from app.database.session import get_session
from app.database.repositories.sync_repository import SyncRepository
from app.services.sync_scheduler import get_sync_scheduler

logger = get_logger(__name__)
sync_bp = Blueprint("sync", __name__)


# ------------------------------------------------------------------
# Job config CRUD
# ------------------------------------------------------------------
@sync_bp.route("/jobs", methods=["GET"])
@login_required
def list_sync_jobs():
    """List all sync job configurations."""
    try:
        source_type = request.args.get("source_type")
        executor_type = request.args.get("executor_type")
        with get_session() as session:
            repo = SyncRepository(session)
            jobs = repo.list_jobs(
                source_type=source_type, executor_type=executor_type
            )
        return jsonify(
            {
                "code": 1,
                "msg": "success",
                "data": [
                    {
                        "id": j.id,
                        "name": j.name,
                        "source_type": j.source_type,
                        "executor_type": j.executor_type,
                        "interval_minutes": j.interval_minutes,
                        "enabled": j.enabled,
                        "last_run_at": j.last_run_at.isoformat()
                        if j.last_run_at
                        else None,
                        "next_run_at": j.next_run_at.isoformat()
                        if j.next_run_at
                        else None,
                        "last_status": j.last_status,
                        "last_error": j.last_error,
                        "config_json": j.config_json,
                        "created_at": j.created_at.isoformat()
                        if j.created_at
                        else None,
                        "updated_at": j.updated_at.isoformat()
                        if j.updated_at
                        else None,
                    }
                    for j in jobs
                ],
            }
        )
    except Exception as e:
        logger.error(f"list_sync_jobs failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e)}), 500


@sync_bp.route("/jobs", methods=["POST"])
@login_required
@admin_required
def create_sync_job():
    """Create a new sync job."""
    try:
        data = request.get_json() or {}
        name = data.get("name", "Data Sync")
        source_type = data.get("source_type", "polymarket")
        executor_type = data.get("executor_type", source_type)
        interval_minutes = data.get("interval_minutes", 30)
        enabled = data.get("enabled", True)
        config_json = data.get("config_json")

        with get_session() as session:
            repo = SyncRepository(session)
            job = repo.create_job(
                name=name,
                source_type=source_type,
                executor_type=executor_type,
                interval_minutes=interval_minutes,
                enabled=enabled,
                config_json=config_json,
            )
        return jsonify(
            {"code": 1, "msg": "success", "data": {"id": job.id}}
        )
    except Exception as e:
        logger.error(f"create_sync_job failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e)}), 500


@sync_bp.route("/jobs/<int:job_id>", methods=["PUT"])
@login_required
@admin_required
def update_sync_job(job_id: int):
    """Update sync job configuration."""
    try:
        data = request.get_json() or {}
        allowed = {
            "name",
            "source_type",
            "executor_type",
            "interval_minutes",
            "enabled",
            "config_json",
        }
        update_data = {k: v for k, v in data.items() if k in allowed}

        with get_session() as session:
            repo = SyncRepository(session)
            job = repo.update_job(job_id, **update_data)
            if job is None:
                return jsonify({"code": 0, "msg": "Job not found"}), 404

        # Restart worker if interval or enabled changed
        if "interval_minutes" in update_data or "enabled" in update_data:
            scheduler = get_sync_scheduler()
            scheduler.stop_job(job_id)
            if job.enabled:
                scheduler.start_job(job)

        return jsonify({"code": 1, "msg": "success", "data": {"id": job_id}})
    except Exception as e:
        logger.error(f"update_sync_job failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e)}), 500


@sync_bp.route("/jobs/<int:job_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_sync_job(job_id: int):
    """Delete a sync job."""
    try:
        scheduler = get_sync_scheduler()
        scheduler.stop_job(job_id)

        with get_session() as session:
            repo = SyncRepository(session)
            deleted = repo.delete_job(job_id)
            if not deleted:
                return jsonify({"code": 0, "msg": "Job not found"}), 404

        return jsonify({"code": 1, "msg": "success"})
    except Exception as e:
        logger.error(f"delete_sync_job failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e)}), 500


# ------------------------------------------------------------------
# Manual trigger
# ------------------------------------------------------------------
@sync_bp.route("/jobs/<int:job_id>/run", methods=["POST"])
@login_required
@admin_required
def run_sync_job(job_id: int):
    """Manually trigger a sync job (async)."""
    try:
        data = request.get_json() or {}
        run_type = data.get("run_type", "incremental")
        limit = data.get("limit")

        scheduler = get_sync_scheduler()
        kwargs = {}
        if limit is not None:
            kwargs["limit"] = limit
        ok = scheduler.trigger_job(job_id, run_type=run_type, **kwargs)

        if not ok:
            return (
                jsonify(
                    {
                        "code": 0,
                        "msg": "Job not found or no executor registered",
                    }
                ),
                404,
            )

        return jsonify(
            {
                "code": 1,
                "msg": "Sync job triggered",
                "data": {"job_id": job_id, "run_type": run_type},
            }
        )
    except Exception as e:
        logger.error(f"run_sync_job failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e)}), 500


# ------------------------------------------------------------------
# Run history
# ------------------------------------------------------------------
@sync_bp.route("/runs", methods=["GET"])
@login_required
def list_sync_runs():
    """Query sync execution history."""
    try:
        job_id = request.args.get("job_id", type=int)
        status = request.args.get("status")
        page = request.args.get("page", 1, type=int)
        page_size = min(request.args.get("page_size", 20, type=int), 100)
        offset = (page - 1) * page_size

        with get_session() as session:
            repo = SyncRepository(session)
            total = repo.count_runs(job_id=job_id, status=status)
            runs = repo.list_runs(
                job_id=job_id, status=status, limit=page_size, offset=offset
            )

        return jsonify(
            {
                "code": 1,
                "msg": "success",
                "data": {
                    "items": [
                        {
                            "id": r.id,
                            "job_id": r.job_id,
                            "run_type": r.run_type,
                            "status": r.status,
                            "started_at": r.started_at.isoformat()
                            if r.started_at
                            else None,
                            "finished_at": r.finished_at.isoformat()
                            if r.finished_at
                            else None,
                            "items_fetched": r.items_fetched,
                            "items_saved": r.items_saved,
                            "items_failed": r.items_failed,
                            "error_message": r.error_message,
                            "detail_json": r.detail_json,
                        }
                        for r in runs
                    ],
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size,
                },
            }
        )
    except Exception as e:
        logger.error(f"list_sync_runs failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e)}), 500


# ------------------------------------------------------------------
# Status
# ------------------------------------------------------------------
@sync_bp.route("/status", methods=["GET"])
@login_required
def get_sync_status():
    """Get current scheduler and workers status."""
    try:
        scheduler = get_sync_scheduler()
        worker_statuses = scheduler.get_all_status()

        with get_session() as session:
            repo = SyncRepository(session)
            jobs = repo.list_jobs()
            latest_runs = {}
            for job in jobs:
                runs = repo.list_runs(job_id=job.id, limit=1, offset=0)
                if runs:
                    r = runs[0]
                    latest_runs[job.id] = {
                        "id": r.id,
                        "status": r.status,
                        "run_type": r.run_type,
                        "started_at": r.started_at.isoformat()
                        if r.started_at
                        else None,
                        "finished_at": r.finished_at.isoformat()
                        if r.finished_at
                        else None,
                        "items_fetched": r.items_fetched,
                        "items_saved": r.items_saved,
                    }

        return jsonify(
            {
                "code": 1,
                "msg": "success",
                "data": {
                    "workers": worker_statuses,
                    "jobs": [
                        {
                            "id": j.id,
                            "name": j.name,
                            "source_type": j.source_type,
                            "executor_type": j.executor_type,
                            "enabled": j.enabled,
                            "interval_minutes": j.interval_minutes,
                            "last_run_at": j.last_run_at.isoformat()
                            if j.last_run_at
                            else None,
                            "last_status": j.last_status,
                            "latest_run": latest_runs.get(j.id),
                        }
                        for j in jobs
                    ],
                },
            }
        )
    except Exception as e:
        logger.error(f"get_sync_status failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e)}), 500


# ------------------------------------------------------------------
# Init default job on first call
# ------------------------------------------------------------------
@sync_bp.route("/init", methods=["POST"])
@login_required
@admin_required
def init_default_job():
    """Initialize default sync jobs if none exist."""
    try:
        with get_session() as session:
            repo = SyncRepository(session)
            jobs = repo.list_jobs()
            if jobs:
                return jsonify(
                    {
                        "code": 1,
                        "msg": "Jobs already exist",
                        "data": {"job_ids": [j.id for j in jobs]},
                    }
                )
            job = repo.create_job(
                name="Polymarket Auto Sync",
                source_type="polymarket",
                executor_type="polymarket",
                interval_minutes=30,
                enabled=True,
            )
            return jsonify(
                {
                    "code": 1,
                    "msg": "Default job created",
                    "data": {"job_id": job.id},
                }
            )
    except Exception as e:
        logger.error(f"init_default_job failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e)}), 500
