"""
Polymarket后台任务
每30分钟更新一次市场数据，并批量分析市场机会
"""
import json
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from app.database.session import get_session
from app.data_sources.polymarket import PolymarketDataSource
from app.services.polymarket_batch_analyzer import PolymarketBatchAnalyzer
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PolymarketWorker:
    """Polymarket数据更新和分析后台任务"""

    def __init__(
        self,
        update_interval_minutes: int = 30,
        analysis_cache_minutes: int = 1440,
        job_id: Optional[int] = None,
    ):
        """
        初始化后台任务

        Args:
            update_interval_minutes: 市场数据更新间隔（分钟）
            analysis_cache_minutes: AI分析结果缓存时间（分钟）
            job_id: 关联的同步任务配置ID
        """
        self.update_interval_minutes = update_interval_minutes
        self.analysis_cache_minutes = analysis_cache_minutes
        self.job_id = job_id or 1
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.polymarket_source = PolymarketDataSource()
        self.batch_analyzer = PolymarketBatchAnalyzer()
        self._last_update_ts = 0.0
        self._current_run_id: Optional[int] = None

    def start(self) -> bool:
        """启动后台任务"""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return True
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop, name="PolymarketWorker", daemon=True
            )
            self._thread.start()
            logger.info(
                f"PolymarketWorker started (update_interval={self.update_interval_minutes}min, "
                f"cache={self.analysis_cache_minutes}min, job_id={self.job_id})"
            )
            return True

    def stop(self, timeout_sec: float = 5.0) -> None:
        """停止后台任务"""
        with self._lock:
            if not self._thread or not self._thread.is_alive():
                return
            self._stop_event.set()
            self._thread.join(timeout=timeout_sec)
            if self._thread.is_alive():
                logger.warning("PolymarketWorker thread did not stop within timeout")
            else:
                logger.info("PolymarketWorker stopped")

    def is_running(self) -> bool:
        """检查Worker是否正在运行"""
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def _run_loop(self) -> None:
        """主循环"""
        logger.info("PolymarketWorker loop started")

        # 启动时立即执行一次
        self._update_markets_and_analyze()

        while not self._stop_event.is_set():
            try:
                wait_seconds = self.update_interval_minutes * 60
                if self._stop_event.wait(wait_seconds):
                    break
                self._update_markets_and_analyze()
            except Exception as e:
                logger.error(f"PolymarketWorker loop error: {e}", exc_info=True)
                self._stop_event.wait(60)

        logger.info("PolymarketWorker loop stopped")

    # ------------------------------------------------------------------
    # Core sync logic
    # ------------------------------------------------------------------
    def _do_sync(
        self,
        run_type: str = "incremental",
        limit: int = 500,
        run_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        执行实际的数据同步

        Args:
            run_type: 'incremental' 或 'full'
            limit: 获取市场数量上限（full 模式下可更大）
            run_id: 可选的执行记录ID（用于更新已有记录）
        """
        start_time = time.time()
        fetched = saved = failed = 0
        error_msg = None
        detail = {"categories": {}}

        try:
            logger.info(
                f"Starting Polymarket {run_type} sync (limit={limit})..."
            )

            all_markets = self.polymarket_source.get_trending_markets(
                category="all", limit=limit
            )
            fetched = len(all_markets)
            logger.info(f"Fetched {fetched} markets from Gamma API")

            unique_markets = {}
            cat_counts: Dict[str, int] = {}
            for market in all_markets:
                mid = market.get("market_id")
                if mid:
                    unique_markets[mid] = market
                    cat = market.get("category", "other")
                    cat_counts[cat] = cat_counts.get(cat, 0) + 1

            detail["categories"] = cat_counts
            saved = len(unique_markets)

            # 2. 批量分析市场（只对增量任务执行，或全量时可选）
            markets_list = list(unique_markets.values())
            if run_type == "incremental" and markets_list:
                rule_based = []
                for m in markets_list:
                    prob = m.get("current_probability", 50.0)
                    volume = m.get("volume_24h", 0)
                    divergence = abs(prob - 50.0)
                    if volume > 5000 and divergence > 8:
                        rule_based.append(m)

                if rule_based:
                    rule_based.sort(
                        key=lambda x: (
                            x.get("volume_24h", 0)
                            * abs(x.get("current_probability", 50) - 50)
                        ),
                        reverse=True,
                    )
                    top_30 = rule_based[:30]
                    analyzed = self.batch_analyzer.batch_analyze_markets(
                        top_30, max_opportunities=30
                    )
                    if analyzed:
                        self.batch_analyzer.save_batch_analysis(analyzed)
                    detail["analyzed_count"] = len(analyzed)
                else:
                    detail["analyzed_count"] = 0

            elapsed = time.time() - start_time
            logger.info(
                f"Polymarket {run_type} sync completed: {saved} markets updated in {elapsed:.1f}s"
            )
            return {
                "status": "success",
                "fetched": fetched,
                "saved": saved,
                "failed": failed,
                "error": None,
                "detail": detail,
                "elapsed_sec": round(elapsed, 2),
            }

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Polymarket sync failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "fetched": fetched,
                "saved": saved,
                "failed": failed,
                "error": error_msg,
                "detail": detail,
                "elapsed_sec": round(elapsed, 2),
            }

    def _update_markets_and_analyze(self) -> None:
        """更新市场数据并分析（定时调用）"""
        from app.database.repositories.polymarket_sync_repository import (
            PolymarketSyncRepository,
        )

        run_id = None
        try:
            with get_session() as session:
                repo = PolymarketSyncRepository(session)
                job = repo.get_job(self.job_id)
                if job and not job.enabled:
                    logger.info("Polymarket sync job is disabled, skipping")
                    return

                run = repo.create_run(
                    job_id=self.job_id,
                    run_type="incremental",
                    status="running",
                )
                run_id = run.id
                self._current_run_id = run_id

            result = self._do_sync(run_type="incremental", run_id=run_id)

            with get_session() as session:
                repo = PolymarketSyncRepository(session)
                repo.update_run(
                    run_id=run_id,
                    status=result["status"],
                    finished_at=datetime.now(),
                    markets_fetched=result["fetched"],
                    markets_saved=result["saved"],
                    markets_failed=result["failed"],
                    error_message=result["error"],
                    detail_json=json.dumps(result["detail"]),
                )
                repo.update_job(
                    self.job_id,
                    last_run_at=datetime.now(),
                    next_run_at=datetime.now()
                    + timedelta(minutes=self.update_interval_minutes),
                    last_status=result["status"],
                    last_error=result["error"],
                )
                self._last_update_ts = time.time()

        except Exception as e:
            logger.error(f"Failed to update markets and analyze: {e}", exc_info=True)
            if run_id:
                try:
                    with get_session() as session:
                        repo = PolymarketSyncRepository(session)
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

    # ------------------------------------------------------------------
    # Public manual triggers
    # ------------------------------------------------------------------
    def force_update(self) -> Dict[str, Any]:
        """强制立即执行增量同步"""
        logger.info("Force incremental sync triggered")
        return self._run_sync_manual("incremental", limit=500)

    def full_sync(self, limit: int = 3000) -> Dict[str, Any]:
        """执行全量同步（拉取更多市场）"""
        logger.info(f"Full sync triggered (limit={limit})")
        return self._run_sync_manual("full", limit=limit)

    def _run_sync_manual(
        self, run_type: str, limit: int
    ) -> Dict[str, Any]:
        """手动触发同步（阻塞执行，带数据库记录）"""
        from app.database.repositories.polymarket_sync_repository import (
            PolymarketSyncRepository,
        )

        run_id = None
        try:
            with get_session() as session:
                repo = PolymarketSyncRepository(session)
                run = repo.create_run(
                    job_id=self.job_id,
                    run_type=run_type,
                    status="running",
                )
                run_id = run.id
                self._current_run_id = run_id

            result = self._do_sync(run_type=run_type, limit=limit, run_id=run_id)

            with get_session() as session:
                repo = PolymarketSyncRepository(session)
                repo.update_run(
                    run_id=run_id,
                    status=result["status"],
                    finished_at=datetime.now(),
                    markets_fetched=result["fetched"],
                    markets_saved=result["saved"],
                    markets_failed=result["failed"],
                    error_message=result["error"],
                    detail_json=json.dumps(result["detail"]),
                )
                repo.update_job(
                    self.job_id,
                    last_run_at=datetime.now(),
                    next_run_at=datetime.now()
                    + timedelta(minutes=self.update_interval_minutes),
                    last_status=result["status"],
                    last_error=result["error"],
                )
                self._last_update_ts = time.time()

            return {**result, "run_id": run_id}
        except Exception as e:
            logger.error(f"Manual sync failed: {e}", exc_info=True)
            if run_id:
                try:
                    with get_session() as session:
                        repo = PolymarketSyncRepository(session)
                        repo.update_run(
                            run_id=run_id,
                            status="failed",
                            finished_at=datetime.now(),
                            error_message=str(e),
                        )
                except Exception:
                    pass
            self._current_run_id = None
            return {
                "status": "failed",
                "fetched": 0,
                "saved": 0,
                "failed": 0,
                "error": str(e),
                "detail": {},
                "elapsed_sec": 0,
                "run_id": run_id,
            }

    def get_status(self) -> Dict[str, Any]:
        """获取当前Worker状态"""
        return {
            "running": self.is_running(),
            "job_id": self.job_id,
            "update_interval_minutes": self.update_interval_minutes,
            "last_update_ts": self._last_update_ts,
            "current_run_id": self._current_run_id,
        }


# 全局单例
_polymarket_worker: Optional[PolymarketWorker] = None
_worker_lock = threading.Lock()


def get_polymarket_worker() -> PolymarketWorker:
    """获取PolymarketWorker单例"""
    global _polymarket_worker
    with _worker_lock:
        if _polymarket_worker is None:
            update_interval = int(
                os.getenv("POLYMARKET_UPDATE_INTERVAL_MIN", "30")
            )
            cache_minutes = int(
                os.getenv("POLYMARKET_ANALYSIS_CACHE_MIN", "30")
            )
            job_id = int(os.getenv("POLYMARKET_SYNC_JOB_ID", "1"))
            _polymarket_worker = PolymarketWorker(
                update_interval_minutes=update_interval,
                analysis_cache_minutes=cache_minutes,
                job_id=job_id,
            )
        return _polymarket_worker
