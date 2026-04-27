"""Simple collector scheduler glue."""
from app.collectors.graph_pipeline import GraphPipeline
from app.collectors.registry import CollectorRegistry
from app.collectors.dedup import DedupEngine


class CollectorScheduler:
    def __init__(self):
        self.registry = CollectorRegistry()
        self.dedup = DedupEngine()
        self.pipeline = GraphPipeline()

    def run_market_collection(self, market: str, symbol: str):
        collector = self.registry.get("market_data")
        collected = collector.collect_all(market=market, symbol=symbol, include_graph_context=True)
        items = self.dedup.filter(collected.get("graph_items") or [])
        return {
            "collected": collected,
            "graph_results": self.pipeline.process_items(items),
        }
