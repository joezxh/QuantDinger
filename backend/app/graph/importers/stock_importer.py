"""Stock market data importer — PostgreSQL → Neo4j."""
from __future__ import annotations

from typing import Any, Dict, List

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
        stock_markets = ('USStock', 'HKStock', 'CNStock', 'Stock')
        try:
            with get_session() as session:
                from app.database.repositories.market_symbol_repository import MarketSymbolRepository
                repo = MarketSymbolRepository(session)
                for market in stock_markets:
                    symbols = repo.list_by_market(market, is_active=1)
                    for sym in symbols:
                        companies.append({
                            "ticker": sym.symbol,
                            "name": sym.name or sym.symbol,
                            "market": sym.market,
                        })
                        if len(companies) >= self.batch_size:
                            break
                    if len(companies) >= self.batch_size:
                        break
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
