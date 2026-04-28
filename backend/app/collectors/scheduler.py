"""Collector scheduler with APScheduler integration.

Supports hourly incremental news ingestion and daily full metadata sync.
"""
import os
from datetime import datetime
from typing import List

from app.collectors.graph_pipeline import GraphPipeline
from app.collectors.registry import CollectorRegistry
from app.collectors.dedup import DedupEngine
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CollectorScheduler:
    """Orchestrate periodic collection and graph ingestion jobs."""

    def __init__(self):
        self.registry = CollectorRegistry()
        self.dedup = DedupEngine()
        self.pipeline = GraphPipeline()
        self._scheduler = None
        self._enabled = os.getenv("COLLECTOR_ENABLED", "true").lower() == "true"

    # ------------------------------------------------------------------
    # Manual invocation (used by API / one-off tasks)
    # ------------------------------------------------------------------
    def run_market_collection(self, market: str, symbol: str):
        collector = self.registry.get("market_data")
        if collector is None:
            logger.error("Market data collector not available")
            return {"collected": {}, "graph_results": []}
        collected = collector.collect_all(market=market, symbol=symbol, include_graph_context=True)
        items = self.dedup.filter(collected.get("graph_items") or [])
        return {
            "collected": collected,
            "graph_results": self.pipeline.process_items(items),
        }

    def run_news_ingestion(self, symbols: List[str], market: str = "USStock"):
        """Hourly incremental: collect news for a batch of symbols and ingest."""
        results = []
        for symbol in symbols:
            try:
                res = self.run_market_collection(market, symbol)
                # Filter to news-only items for lightweight ingestion
                news_results = [
                    r for r in res.get("graph_results", [])
                    if r.get("status") in ("completed", "episode_exists")
                ]
                results.append({"symbol": symbol, "news_ingested": len(news_results)})
            except Exception as e:
                logger.warning("News ingestion failed for %s:%s — %s", market, symbol, e)
                results.append({"symbol": symbol, "error": str(e)})
        logger.info("Hourly news ingestion finished: %s symbols", len(symbols))
        return results

    def run_daily_metadata_sync(self):
        """Daily full sync: run all domain importers to refresh Neo4j nodes."""
        counters = {}
        try:
            from app.graph.importers.stock_importer import StockGraphImporter
            counters["stock"] = StockGraphImporter().import_batch()
        except Exception as e:
            logger.warning("Daily stock metadata sync failed: %s", e)
            counters["stock"] = {"error": str(e)}

        try:
            from app.graph.importers.crypto_importer import CryptoGraphImporter
            counters["crypto"] = CryptoGraphImporter().import_batch()
        except Exception as e:
            logger.warning("Daily crypto metadata sync failed: %s", e)
            counters["crypto"] = {"error": str(e)}

        try:
            from app.graph.importers.polymarket_importer import PolymarketGraphImporter
            counters["polymarket"] = PolymarketGraphImporter().import_batch()
        except Exception as e:
            logger.warning("Daily polymarket metadata sync failed: %s", e)
            counters["polymarket"] = {"error": str(e)}

        logger.info("Daily metadata sync finished: %s", counters)
        return counters

    # ------------------------------------------------------------------
    # APScheduler integration
    # ------------------------------------------------------------------
    def start(self):
        """Start background scheduler if enabled."""
        if not self._enabled:
            logger.info("Collector scheduler is disabled (COLLECTOR_ENABLED=false)")
            return

        if self._scheduler is not None:
            logger.warning("Scheduler already started")
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.warning("APScheduler not installed — periodic collection disabled")
            return

        self._scheduler = BackgroundScheduler()

        # Hourly incremental news ingestion (top 20 hot symbols)
        self._scheduler.add_job(
            self._hourly_news_job,
            trigger=CronTrigger(minute=0),  # top of every hour
            id="graph_hourly_news",
            replace_existing=True,
        )

        # Daily full metadata sync at 02:00 UTC
        self._scheduler.add_job(
            self.run_daily_metadata_sync,
            trigger=CronTrigger(hour=2, minute=0),
            id="graph_daily_metadata",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("Collector scheduler started — hourly news + daily metadata sync")

    def shutdown(self):
        """Gracefully shut down the scheduler."""
        if self._scheduler:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            logger.info("Collector scheduler shut down")

    def _hourly_news_job(self):
        """Pick hot symbols and run news ingestion."""
        symbols = self._get_hot_symbols("USStock", limit=10)
        symbols += self._get_hot_symbols("Crypto", limit=10)
        if not symbols:
            logger.info("No hot symbols for hourly news ingestion")
            return
        self.run_news_ingestion(symbols)

    def _get_hot_symbols(self, market: str, limit: int = 10) -> List[str]:
        """Fetch active hot symbols from the database."""
        try:
            from app.database.session import get_session
            from app.database.repositories.market_symbol_repository import MarketSymbolRepository
            with get_session() as session:
                repo = MarketSymbolRepository(session)
                syms = repo.list_hot_by_market(market, limit=limit)
                return [s.symbol for s in syms]
        except Exception as e:
            logger.warning("Failed to fetch hot symbols for %s: %s", market, e)
            return []
