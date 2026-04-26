"""Polymarket data importer — PostgreSQL → Neo4j."""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from app.database.session import get_session
from app.graph.importers.base import BaseGraphImporter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PolymarketGraphImporter(BaseGraphImporter):
    """Import Polymarket prediction market data into the knowledge graph."""

    def import_batch(self) -> Dict[str, int]:
        counters = {"markets": 0, "users": 0, "trades": 0}

        markets = self._fetch_markets()
        if markets:
            counters["markets"] = self._run_merge_nodes("PredictionMarket", "market_id", markets)
            logger.info("Imported %s polymarket markets", counters["markets"])

        users = self._fetch_users()
        if users:
            counters["users"] = self._run_merge_nodes("PolymarketUser", "address", users)
            logger.info("Imported %s polymarket users", counters["users"])

        trades = self._fetch_trades()
        if trades:
            counters["trades"] = self._run_merge_relationships(
                "TRADED_IN", "PolymarketUser", "address", "PredictionMarket", "market_id", trades
            )
            logger.info("Imported %s trade relationships", counters["trades"])

        return counters

    def _fetch_markets(self) -> List[Dict[str, Any]]:
        """Fetch Polymarket markets from qd_polymarket_markets."""
        markets: List[Dict[str, Any]] = []
        try:
            with get_session() as session:
                result = session.execute(
                    text("""
                        SELECT id, market_id, question, category, resolution
                        FROM qd_polymarket_markets
                        LIMIT :limit
                    """),
                    {"limit": self.batch_size},
                )
                for row in result.mappings():
                    markets.append({
                        "market_id": str(row["market_id"]),
                        "question": row["question"] or "",
                        "category": row["category"],
                        "resolution": row["resolution"],
                    })
        except Exception as e:
            logger.warning("Fetch polymarket markets failed: %s", e)
        return markets

    def _fetch_users(self) -> List[Dict[str, Any]]:
        """Fetch Polymarket users from qd_polymarket_users."""
        users: List[Dict[str, Any]] = []
        try:
            with get_session() as session:
                result = session.execute(
                    text("""
                        SELECT address, win_rate, profit
                        FROM qd_polymarket_users
                        LIMIT :limit
                    """),
                    {"limit": self.batch_size},
                )
                for row in result.mappings():
                    users.append({
                        "address": row["address"],
                        "win_rate": float(row["win_rate"]) if row["win_rate"] else 0.0,
                        "profit": float(row["profit"]) if row["profit"] else 0.0,
                    })
        except Exception as e:
            logger.warning("Fetch polymarket users failed: %s", e)
        return users

    def _fetch_trades(self) -> List[Dict[str, Any]]:
        """Placeholder: user-market trade relationships."""
        return []
