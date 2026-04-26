"""Domain graph services for stock, crypto and polymarket."""
from typing import Dict

from app.graph.queries import (
    get_crypto_kol_consensus,
    get_polymarket_smart_money,
    get_recent_events,
    get_stock_holders,
)
from app.services.graph_feature_writer import GraphFeatureWriter


class _BaseDomainGraphService:
    market_name = ""
    source_name = ""

    def __init__(self, feature_writer=None):
        self.feature_writer = feature_writer or GraphFeatureWriter()

    def write_daily_features(self, symbol: str, features: dict) -> int:
        return self.feature_writer.write_daily_features(
            market=self.market_name,
            symbol=symbol,
            source=self.source_name,
            features=features,
        )


class StockGraphService(_BaseDomainGraphService):
    market_name = "USStock"
    source_name = "stock_graph_service"

    def get_company_graph(self, ticker: str) -> Dict:
        return {
            "ticker": ticker,
            "holders": get_stock_holders(ticker),
            "recent_events": get_recent_events(ticker),
        }

    def write_narrative_features(self, ticker: str, features: dict) -> int:
        return self.feature_writer.write_company_narrative_features(
            ticker=ticker,
            source=self.source_name,
            features=features,
        )


class CryptoGraphService(_BaseDomainGraphService):
    market_name = "Crypto"
    source_name = "crypto_graph_service"

    def get_asset_graph(self, symbol: str) -> Dict:
        return {
            "symbol": symbol,
            "kol_consensus": get_crypto_kol_consensus(symbol),
            "recent_events": get_recent_events(symbol),
        }

    def write_narrative_features(self, symbol: str, features: dict) -> int:
        return self.feature_writer.write_crypto_narrative_features(
            symbol=symbol,
            source=self.source_name,
            features=features,
        )


class PolymarketGraphService(_BaseDomainGraphService):
    market_name = "Polymarket"
    source_name = "polymarket_graph_service"

    def get_market_graph(self, market_id: str) -> Dict:
        return {
            "market_id": market_id,
            "smart_money": get_polymarket_smart_money(market_id),
        }

    def write_market_features(self, market_id: str, features: dict) -> int:
        return self.feature_writer.write_polymarket_market_features(
            market_id=market_id,
            source=self.source_name,
            features=features,
        )
