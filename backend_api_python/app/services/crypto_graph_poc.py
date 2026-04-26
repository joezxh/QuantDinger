"""Crypto graph proof-of-concept service."""
from typing import Any, Dict

from app.collectors.dedup import DedupEngine
from app.collectors.storage import CollectorStorage
from app.services.domain_graph_services import CryptoGraphService
from app.services.market_data_collector import get_market_data_collector


class CryptoGraphPocService:
    def __init__(self, collector_storage=None, dedup_engine=None, graph_service=None):
        self.collector = get_market_data_collector()
        self.storage = collector_storage or CollectorStorage()
        self.dedup = dedup_engine or DedupEngine(collector_storage=self.storage)
        self.service = graph_service or CryptoGraphService()

    def run(self, symbol: str = "ETH/USDT") -> Dict[str, Any]:
        collected = self.collector.collect_all(
            market="Crypto",
            symbol=symbol,
            timeframe="1D",
            include_macro=True,
            include_news=True,
            include_polymarket=False,
            include_graph_context=True,
        )
        graph_items = self.dedup.filter(collected.get("graph_items", []))
        graph = self.service.get_asset_graph(symbol)
        daily_feature_count = self.service.write_daily_features(symbol, {"graph_signal_strength": 0.0})
        narrative_feature_count = self.service.write_narrative_features(
            symbol,
            {
                "kol_consensus_strength": len(graph.get("kol_consensus") or []),
            },
        )
        return {
            "symbol": symbol,
            "graph": graph,
            "graph_context": collected.get("graph_context", {}),
            "graph_items": graph_items,
            "written_feature_count": daily_feature_count,
            "written_narrative_feature_count": narrative_feature_count,
        }
