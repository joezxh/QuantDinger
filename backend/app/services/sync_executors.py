"""
Concrete sync task executors.
Each executor implements the SyncTaskExecutor interface for a specific datasource.
"""
import time
from typing import Dict, Any

from app.data_sources.polymarket import PolymarketDataSource
from app.models.sync_task import SyncJob, SyncRun
from app.services.polymarket_batch_analyzer import PolymarketBatchAnalyzer
from app.services.sync_scheduler import SyncTaskExecutor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PolymarketSyncExecutor(SyncTaskExecutor):
    """Executor for Polymarket data sync."""

    def __init__(self):
        self.polymarket_source = PolymarketDataSource()
        self.batch_analyzer = PolymarketBatchAnalyzer()

    @property
    def source_type(self) -> str:
        return "polymarket"

    def execute(
        self,
        job: SyncJob,
        run: SyncRun,
        run_type: str = "incremental",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        start_time = time.time()
        fetched = saved = failed = 0
        detail = {"categories": {}}

        try:
            limit = kwargs.get("limit", 3000 if run_type == "full" else 500)
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

            # Batch analysis for incremental runs
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
                f"Polymarket {run_type} sync completed: "
                f"{saved} markets updated in {elapsed:.1f}s"
            )
            return {
                "status": "success",
                "items_fetched": fetched,
                "items_saved": saved,
                "items_failed": failed,
                "error": None,
                "detail": detail,
                "elapsed_sec": round(elapsed, 2),
            }

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Polymarket sync failed: {e}", exc_info=True)
            return {
                "status": "failed",
                "items_fetched": fetched,
                "items_saved": saved,
                "items_failed": failed,
                "error": str(e),
                "detail": detail,
                "elapsed_sec": round(elapsed, 2),
            }
