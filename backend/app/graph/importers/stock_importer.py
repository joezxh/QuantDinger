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
        """Seed top-tier asset managers as baseline institution nodes.

        In production this would be replaced by 13F / ownership API feeds.
        """
        seeds = [
            {"name": "BlackRock", "type": "资产管理", "aum_billion": 10500},
            {"name": "Vanguard", "type": "指数基金", "aum_billion": 8700},
            {"name": "State Street", "type": "托管银行", "aum_billion": 4200},
            {"name": "Fidelity", "type": "共同基金", "aum_billion": 4800},
            {"name": "Berkshire Hathaway", "type": "保险/控股", "aum_billion": 900},
        ]
        return seeds

    def _fetch_holdings(self) -> List[Dict[str, Any]]:
        """Seed representative holdings for demo / baseline graph edges.

        In production this would come from quarterly 13F filings or ownership APIs.
        Maps seed institutions to tickers that exist in the market_symbols table.
        """
        # Common large-cap holdings across major institutions
        holdings_map = {
            "BlackRock": ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "BRK-B"],
            "Vanguard": ["AAPL", "MSFT", "AMZN", "TSLA", "GOOGL", "BRK-B", "JNJ", "UNH"],
            "State Street": ["AAPL", "MSFT", "NVDA", "JPM", "XOM", "JNJ", "V", "PG"],
            "Fidelity": ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "NFLX", "AMD"],
            "Berkshire Hathaway": ["AAPL", "BAC", "KO", "AXP", "CVX", "OXY", "KHC", "MCO"],
        }
        holdings: List[Dict[str, Any]] = []
        try:
            with get_session() as session:
                from app.database.repositories.market_symbol_repository import MarketSymbolRepository
                repo = MarketSymbolRepository(session)
                available_tickers = {
                    s.symbol for s in repo.list_by_market("USStock", is_active=1)
                }
        except Exception:
            available_tickers = set()

        for inst, tickers in holdings_map.items():
            for tkr in tickers:
                if available_tickers and tkr not in available_tickers:
                    continue
                holdings.append({
                    "from_id": inst,
                    "to_id": tkr,
                    "props": {"source": "seed", "confidence": 0.85},
                })
                if len(holdings) >= self.batch_size:
                    break
            if len(holdings) >= self.batch_size:
                break
        return holdings
