"""Stock market data importer — PostgreSQL → Neo4j."""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from app.database.session import get_session
from app.graph.importers.base import BaseGraphImporter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StockGraphImporter(BaseGraphImporter):
    """Import stock-related entities and relationships into the knowledge graph."""

    def import_batch(self) -> Dict[str, int]:
        counters = {"companies": 0, "institutions": 0, "holds": 0}

        # 1. Import companies from qd_indicator_codes (stock-related) and market symbols
        companies = self._fetch_companies()
        if companies:
            counters["companies"] = self._run_merge_nodes("Company", "ticker", companies)
            logger.info("Imported %s companies", counters["companies"])

        # 2. Import institutions (placeholder — would come from external ownership data)
        institutions = self._fetch_institutions()
        if institutions:
            counters["institutions"] = self._run_merge_nodes("Institution", "name", institutions)
            logger.info("Imported %s institutions", counters["institutions"])

        # 3. Import HOLD relationships
        holds = self._fetch_holdings()
        if holds:
            counters["holds"] = self._run_merge_relationships(
                "HOLDS_SHARES", "Institution", "name", "Company", "ticker", holds
            )
            logger.info("Imported %s hold relationships", counters["holds"])

        return counters

    def _fetch_companies(self) -> List[Dict[str, Any]]:
        """Fetch stock company candidates from market symbols and indicators."""
        companies: List[Dict[str, Any]] = []
        try:
            with get_session() as session:
                # From market symbols (stock markets)
                result = session.execute(
                    text("""
                        SELECT symbol, name, market
                        FROM qd_market_symbols
                        WHERE market IN ('USStock', 'HKStock', 'CNStock', 'Stock')
                        LIMIT :limit
                    """),
                    {"limit": self.batch_size},
                )
                for row in result.mappings():
                    companies.append({
                        "ticker": row["symbol"],
                        "name": row["name"] or row["symbol"],
                        "market": row["market"],
                    })
        except Exception as e:
            logger.warning("Fetch companies failed: %s", e)
        return companies

    def _fetch_institutions(self) -> List[Dict[str, Any]]:
        """Placeholder: in production this would load from ownership / 13F datasets."""
        # For now, return an empty list; real data would come from external APIs
        return []

    def _fetch_holdings(self) -> List[Dict[str, Any]]:
        """Placeholder: institution-company holdings."""
        return []
