"""Stock news graph proof-of-concept service."""
from typing import Any, Dict

from app.collectors.dedup import DedupEngine
from app.collectors.graph_pipeline import GraphPipeline
from app.collectors.storage import CollectorStorage
from app.services.domain_graph_services import StockGraphService
from app.services.market_data_collector import get_market_data_collector


class StockNewsGraphPocService:
    def __init__(self, collector_storage=None, dedup_engine=None, graph_pipeline=None, graph_service=None):
        self.collector = get_market_data_collector()
        self.storage = collector_storage or CollectorStorage()
        self.dedup = dedup_engine or DedupEngine(collector_storage=self.storage)
        self.pipeline = graph_pipeline or GraphPipeline(collector_storage=self.storage)
        self.service = graph_service or StockGraphService()

    def run(self, symbol: str = "NVDA", market: str = "USStock") -> Dict[str, Any]:
        collected = self.collector.collect_all(
            market=market,
            symbol=symbol,
            timeframe="1D",
            include_macro=False,
            include_news=True,
            include_polymarket=False,
            include_graph_context=True,
        )
        items = self.collector.build_graph_collected_items(market, symbol, collected)
        items = self.dedup.filter(items)

        records = []
        graph_results = []
        storage_error = None
        graph_error = None

        try:
            records = self.storage.save_collection_records(items)
        except Exception as e:
            storage_error = str(e)

        try:
            graph_results = self.pipeline.process_items(items)
        except Exception as e:
            graph_error = str(e)

        stock_graph = self.service.get_company_graph(symbol)
        narrative_feature_count = self.service.write_narrative_features(
            symbol,
            {
                "holder_count": len(stock_graph.get("holders") or []),
            },
        )

        return {
            "market": market,
            "symbol": symbol,
            "collection_count": len(records),
            "graph_job_count": len(graph_results),
            "graph_results": graph_results,
            "graph_context": collected.get("graph_context", {}),
            "stock_graph": stock_graph,
            "written_narrative_feature_count": narrative_feature_count,
            "storage_error": storage_error,
            "graph_error": graph_error,
        }
