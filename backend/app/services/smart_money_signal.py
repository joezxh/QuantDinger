"""Smart money signal aggregator — polymarket, whale, institutional flows."""
from typing import Any, Dict, List, Optional

from app.graph.connection import run_cypher
from app.graph.cache_gateway import GraphCacheGateway
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SmartMoneySignal:
    """Aggregate smart-money signals across stock, crypto, and prediction markets.

    Results are cached via GraphCacheGateway to reduce Neo4j query load.
    """

    def __init__(self, cache: Optional[GraphCacheGateway] = None):
        self.cache = cache or GraphCacheGateway()

    # ------------------------------------------------------------------
    # Polymarket smart money
    # ------------------------------------------------------------------
    def get_polymarket_smart_money(self, market_id: str) -> Dict[str, Any]:
        """Aggregate top-trader signals for a Polymarket event.

        Returns consensus direction, top users, and confidence score.
        """
        cache_key = f"graph:smart-money:polymarket:{market_id}"
        cached = self.cache.cache.get(cache_key)
        if cached:
            return cached

        top_users = self._query_pm_top_users(market_id)
        consensus = self._compute_pm_consensus(top_users)

        result = {
            "market_id": market_id,
            "domain": "polymarket",
            "consensus": consensus.get("direction", "neutral"),
            "confidence": consensus.get("confidence", 0),
            "top_users": top_users[:10],
            "user_count": len(top_users),
        }
        self.cache.cache.set(cache_key, result, ttl=1800)
        return result

    def _query_pm_top_users(self, market_id: str) -> List[Dict[str, Any]]:
        query = """
            MATCH (u:PolymarketUser)-[t:TRADED_IN]->(pm:PredictionMarket {market_id: $market_id})
            RETURN u.address AS address,
                   u.display_name AS name,
                   u.win_rate AS win_rate,
                   u.volume AS volume,
                   t.direction AS direction,
                   t.amount AS amount
            ORDER BY coalesce(u.win_rate, 0) DESC, coalesce(t.amount, 0) DESC
            LIMIT 20
        """
        try:
            return run_cypher(query, {"market_id": market_id}) or []
        except Exception as e:
            logger.warning("Polymarket smart-money query failed: %s", e)
            return []

    def _compute_pm_consensus(self, users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple consensus: weighted by win_rate * amount."""
        if not users:
            return {"direction": "neutral", "confidence": 0}

        yes_weight = 0.0
        no_weight = 0.0
        for u in users:
            direction = (u.get("direction") or "").lower()
            weight = float(u.get("win_rate") or 0) * float(u.get("amount") or 1)
            if direction in ("yes", "buy", "long"):
                yes_weight += weight
            elif direction in ("no", "sell", "short"):
                no_weight += weight

        total = yes_weight + no_weight
        if total == 0:
            return {"direction": "neutral", "confidence": 0}

        if yes_weight > no_weight:
            direction = "yes"
            confidence = round((yes_weight / total) * 100, 2)
        else:
            direction = "no"
            confidence = round((no_weight / total) * 100, 2)
        return {"direction": direction, "confidence": confidence}

    # ------------------------------------------------------------------
    # Whale accumulation (crypto)
    # ------------------------------------------------------------------
    def get_whale_accumulation(self, symbol: str) -> Dict[str, Any]:
        """Detect whale wallet accumulation or distribution for a crypto asset.

        Returns accumulation_score, whale_count, and top mover list.
        """
        cache_key = f"graph:smart-money:crypto:{symbol}"
        cached = self.cache.cache.get(cache_key)
        if cached:
            return cached

        whales = self._query_whale_holds(symbol)
        score, trend = self._score_whale_trend(whales)

        result = {
            "symbol": symbol,
            "domain": "crypto",
            "trend": trend,
            "accumulation_score": score,
            "whale_count": len(whales),
            "top_whales": whales[:10],
        }
        self.cache.cache.set(cache_key, result, ttl=1800)
        return result

    def _query_whale_holds(self, symbol: str) -> List[Dict[str, Any]]:
        query = """
            MATCH (w:CryptoAccount {label: 'whale'})-[h:HOLDS]->(a:Asset {symbol: $symbol, market: 'Crypto'})
            RETURN w.address AS address,
                   w.handle AS handle,
                   h.balance AS balance,
                   h.balance_change_7d AS change_7d,
                   h.balance_change_30d AS change_30d
            ORDER BY coalesce(h.balance, 0) DESC
            LIMIT 20
        """
        try:
            return run_cypher(query, {"symbol": symbol}) or []
        except Exception as e:
            logger.warning("Whale accumulation query failed: %s", e)
            return []

    def _score_whale_trend(self, whales: List[Dict[str, Any]]) -> tuple[float, str]:
        """Score based on 7d/30d balance changes across top whales."""
        if not whales:
            return 0.0, "neutral"

        total_7d = 0.0
        total_30d = 0.0
        for w in whales:
            total_7d += float(w.get("change_7d") or 0)
            total_30d += float(w.get("change_30d") or 0)

        avg_7d = total_7d / len(whales)
        avg_30d = total_30d / len(whales)

        # Normalize rough score 0-100
        score = min(100.0, max(0.0, 50.0 + avg_7d * 5 + avg_30d * 2))
        if score > 60:
            trend = "accumulating"
        elif score < 40:
            trend = "distributing"
        else:
            trend = "neutral"
        return round(score, 2), trend

    # ------------------------------------------------------------------
    # Institutional flow (stock)
    # ------------------------------------------------------------------
    def get_institutional_flow(self, ticker: str) -> Dict[str, Any]:
        """Detect institutional inflow / outflow for a stock ticker.

        Returns flow_direction, net_institution_count, and top holders.
        """
        cache_key = f"graph:smart-money:stock:{ticker}"
        cached = self.cache.cache.get(cache_key)
        if cached:
            return cached

        holders = self._query_institutional_holders(ticker)
        direction, score = self._score_institutional_flow(holders)

        result = {
            "ticker": ticker,
            "domain": "stock",
            "flow_direction": direction,
            "flow_score": score,
            "holder_count": len(holders),
            "top_holders": holders[:10],
        }
        self.cache.cache.set(cache_key, result, ttl=1800)
        return result

    def _query_institutional_holders(self, ticker: str) -> List[Dict[str, Any]]:
        query = """
            MATCH (i:Institution)-[h:HOLDS_SHARES]->(c:Company {ticker: $ticker})
            RETURN i.name AS institution,
                   i.type AS type,
                   h.shares AS shares,
                   h.change_qoq AS change_qoq,
                   h.weight_pct AS weight_pct
            ORDER BY coalesce(h.shares, 0) DESC
            LIMIT 20
        """
        try:
            return run_cypher(query, {"ticker": ticker}) or []
        except Exception as e:
            logger.warning("Institutional flow query failed: %s", e)
            return []

    def _score_institutional_flow(self, holders: List[Dict[str, Any]]) -> tuple[str, float]:
        """Score based on QoP share changes across top holders."""
        if not holders:
            return "neutral", 50.0

        total_change = 0.0
        for h in holders:
            total_change += float(h.get("change_qoq") or 0)

        avg_change = total_change / len(holders)
        score = min(100.0, max(0.0, 50.0 + avg_change * 10))
        if score > 60:
            direction = "inflow"
        elif score < 40:
            direction = "outflow"
        else:
            direction = "neutral"
        return direction, round(score, 2)
