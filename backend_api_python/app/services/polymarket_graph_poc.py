"""Polymarket graph proof-of-concept service."""
from typing import Any, Dict

from app.collectors.dedup import DedupEngine
from app.collectors.storage import CollectorStorage
from app.services.domain_graph_services import PolymarketGraphService
from app.services.market_data_collector import get_market_data_collector


class PolymarketGraphPocService:
    def __init__(self, collector_storage=None, dedup_engine=None, graph_service=None):
        self.collector = get_market_data_collector()
        self.storage = collector_storage or CollectorStorage()
        self.dedup = dedup_engine or DedupEngine(collector_storage=self.storage)
        self.service = graph_service or PolymarketGraphService()

    def run(self, market_id: str = "12345") -> Dict[str, Any]:
        collected = self.collector.collect_all(
            market="Polymarket",
            symbol=market_id,
            timeframe="1D",
            include_macro=False,
            include_news=False,
            include_polymarket=True,
            include_graph_context=True,
        )
        graph_items = self.dedup.filter(collected.get("graph_items", []))
        graph = self.service.get_market_graph(market_id)
        daily_feature_count = self.service.write_daily_features(market_id, {"smart_money_score": 0.0})
        market_feature_count = self.service.write_market_features(
            market_id,
            {
                "smart_money_accounts": len((graph.get("smart_money") or [])),
            },
        )
        return {
            "market_id": market_id,
            "graph": graph,
            "graph_context": collected.get("graph_context", {}),
            "graph_items": graph_items,
            "written_feature_count": daily_feature_count,
            "written_market_feature_count": market_feature_count,
        }
