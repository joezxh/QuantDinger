"""Graphiti ontologies for QuantDinger knowledge graph domains.

Exports domain-specific entity models used by Graphiti episode ingestion
and Cypher-based graph queries.
"""
from app.graph.ontologies.stock import Company, Executive, Institution
from app.graph.ontologies.crypto import CryptoAsset, Protocol, CryptoAccount
from app.graph.ontologies.polymarket import PredictionMarket, MarketOutcome

__all__ = [
    "Company",
    "Executive",
    "Institution",
    "CryptoAsset",
    "Protocol",
    "CryptoAccount",
    "PredictionMarket",
    "MarketOutcome",
]
