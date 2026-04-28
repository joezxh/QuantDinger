"""Cryptocurrency data importer — PostgreSQL → Neo4j."""
from __future__ import annotations

from typing import Any, Dict, List

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
                from app.database.repositories.market_symbol_repository import MarketSymbolRepository
                repo = MarketSymbolRepository(session)
                symbols = repo.list_by_market("Crypto", is_active=1)
                for sym in symbols[:self.batch_size]:
                    assets.append({
                        "symbol": sym.symbol,
                        "name": sym.name or sym.symbol,
                        "market": "Crypto",
                    })
        except Exception as e:
            logger.warning("Fetch crypto assets failed: %s", e)
        return assets

    def _fetch_accounts(self) -> List[Dict[str, Any]]:
        """Seed well-known crypto whales / KOLs as baseline account nodes.

        In production this would come from on-chain labeling APIs (e.g. Nansen,
        Arkham, Etherscan tags) or social-graph crawlers.
        """
        seeds = [
            {"address": "0x0000000000000000000000000000000000000000", "handle": "null_address", "platform": "on-chain", "label": "burn"},
            {"address": "0x71C7656EC7ab88b098defB751B7401B5f6d8976F", "handle": "vitalik.eth", "platform": "Twitter", "label": "kol", "followers": 5200000},
            {"address": "0x3Bdd8dC8B53A5C62B062A2F4d76D6b72A31A87B1", "handle": "cz_binance", "platform": "Twitter", "label": "kol", "followers": 8700000},
            {"address": "0x267be1C1D684F078cb4D97c2955E6C095E207fA6", "handle": "saylor", "platform": "Twitter", "label": "kol", "followers": 3100000},
            {"address": "0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8", "handle": "binance_cold", "platform": "on-chain", "label": "cex"},
        ]
        return seeds

    def _fetch_holdings(self) -> List[Dict[str, Any]]:
        """Seed representative crypto holdings for demo / baseline graph edges.

        In production this would come from on-chain balance snapshots.
        """
        holdings_map = {
            "vitalik.eth": ["ETH/USDT", "MKR/USDT", "UNI/USDT"],
            "cz_binance": ["BNB/USDT", "BTC/USDT", "ETH/USDT"],
            "saylor": ["BTC/USDT", "MSTR"],
            "binance_cold": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "USDT/USDT"],
        }
        holdings: List[Dict[str, Any]] = []
        try:
            with get_session() as session:
                from app.database.repositories.market_symbol_repository import MarketSymbolRepository
                repo = MarketSymbolRepository(session)
                available_symbols = {
                    s.symbol for s in repo.list_by_market("Crypto", is_active=1)
                }
        except Exception:
            available_symbols = set()

        for handle, symbols in holdings_map.items():
            for sym in symbols:
                if available_symbols and sym not in available_symbols:
                    continue
                holdings.append({
                    "from_id": handle,
                    "to_id": sym,
                    "props": {"source": "seed", "confidence": 0.7},
                })
                if len(holdings) >= self.batch_size:
                    break
            if len(holdings) >= self.batch_size:
                break
        return holdings
