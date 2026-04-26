"""Graph query helpers by domain."""
from typing import Any, Dict, List

from app.graph.connection import run_cypher


def _safe_query(query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return run_cypher(query, params) or []
    except Exception:
        return []


def find_related_assets(symbol: str, market: str, depth: int = 2) -> List[Dict[str, Any]]:
    return _safe_query(
        """
        MATCH (a:Asset {symbol: $symbol, market: $market})-[:CORRELATED_WITH]-(other:Asset)
        RETURN other.symbol AS symbol, other.market AS market
        LIMIT 5
        """,
        {"symbol": symbol, "market": market, "depth": depth},
    )


def get_recent_events(symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
    return _safe_query(
        """
        MATCH (e:Event)-[:AFFECTS]->(a:Asset {symbol: $symbol})
        RETURN e.title AS title, e.event_time AS event_time
        ORDER BY e.event_time DESC
        LIMIT $limit
        """,
        {"symbol": symbol, "limit": limit},
    )


def get_prediction_market_signals(symbol: str) -> List[Dict[str, Any]]:
    return _safe_query(
        """
        MATCH (a:Asset {symbol: $symbol})<-[:LINKED_TO_ASSET]-(pm:PredictionMarket)
        RETURN pm.question AS question, pm.probability AS probability
        LIMIT 5
        """,
        {"symbol": symbol},
    )


def get_stock_holders(ticker: str) -> List[Dict[str, Any]]:
    return _safe_query(
        """
        MATCH (co:Company {ticker: $ticker})<-[:HOLDS_SHARES]-(inst:Institution)
        RETURN inst.name AS institution
        LIMIT 5
        """,
        {"ticker": ticker},
    )


def get_crypto_kol_consensus(symbol: str) -> List[Dict[str, Any]]:
    return _safe_query(
        """
        MATCH (ca:CryptoAccount)-[:HOLDS]->(a:Asset {symbol: $symbol, market: 'Crypto'})
        RETURN count(ca) AS kol_count
        LIMIT 1
        """,
        {"symbol": symbol},
    )


def get_polymarket_smart_money(market_id: str) -> List[Dict[str, Any]]:
    return _safe_query(
        """
        MATCH (u:PolymarketUser)-[:TRADED_IN]->(pm:PredictionMarket {market_id: $market_id})
        RETURN u.address AS address, u.win_rate AS win_rate
        LIMIT 10
        """,
        {"market_id": market_id},
    )
