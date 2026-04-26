"""Cryptocurrency data importer — PostgreSQL → Neo4j."""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text

from app.database.session import get_session
from app.graph.importers.base import BaseGraphImporter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CryptoGraphImporter(BaseGraphImporter):
    """Import crypto-related entities and relationships into the knowledge graph."""

    def import_batch(self) -> Dict[str, int]:
        counters = {"assets": 0, "accounts": 0, "holds": 0}

        assets = self._fetch_assets()
        if assets:
            counters["assets"] = self._run_merge_nodes("Asset", "symbol", assets)
            logger.info("Imported %s crypto assets", counters["assets"])

        accounts = self._fetch_accounts()
        if accounts:
            counters["accounts"] = self._run_merge_nodes("CryptoAccount", "address", accounts)
            logger.info("Imported %s crypto accounts", counters["accounts"])

        holds = self._fetch_holdings()
        if holds:
            counters["holds"] = self._run_merge_relationships(
                "HOLDS", "CryptoAccount", "address", "Asset", "symbol", holds
            )
            logger.info("Imported %s hold relationships", counters["holds"])

        return counters

    def _fetch_assets(self) -> List[Dict[str, Any]]:
        """Fetch crypto assets from market symbols."""
        assets: List[Dict[str, Any]] = []
        try:
            with get_session() as session:
                result = session.execute(
                    text("""
                        SELECT symbol, name
                        FROM qd_market_symbols
                        WHERE market = 'Crypto'
                        LIMIT :limit
                    """),
                    {"limit": self.batch_size},
                )
                for row in result.mappings():
                    assets.append({
                        "symbol": row["symbol"],
                        "name": row["name"] or row["symbol"],
                        "market": "Crypto",
                    })
        except Exception as e:
            logger.warning("Fetch crypto assets failed: %s", e)
        return assets

    def _fetch_accounts(self) -> List[Dict[str, Any]]:
        """Placeholder: whale / KOL accounts from on-chain or social data."""
        return []

    def _fetch_holdings(self) -> List[Dict[str, Any]]:
        """Placeholder: account-asset holdings."""
        return []
