"""Event impact analyzer — contagion paths, event tracing, cascade risk."""
from typing import Any, Dict, List, Optional

from app.graph.connection import run_cypher
from app.graph.cache_gateway import GraphCacheGateway
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EventImpactAnalyzer:
    """Analyze how events propagate across the knowledge graph.

    All methods gracefully degrade to empty results when Neo4j is unavailable.
    """

    def __init__(self, cache: Optional[GraphCacheGateway] = None):
        self.cache = cache or GraphCacheGateway()

    # ------------------------------------------------------------------
    # Contagion path
    # ------------------------------------------------------------------
    def get_contagion_path(
        self, from_symbol: str, to_symbol: str, market: str = "Crypto", max_depth: int = 4
    ) -> Dict[str, Any]:
        """Find the shortest/multi-hop path(s) between two assets.

        Returns a dict with ``paths`` (list of node chains) and ``risk_score``.
        """
        cache_key = f"graph:contagion:{market}:{from_symbol}:{to_symbol}"
        cached = self.cache.cache.get(cache_key)
        if cached:
            return cached

        paths = self._query_paths(from_symbol, to_symbol, market, max_depth)
        risk_score = self._score_paths(paths)

        result = {
            "from": from_symbol,
            "to": to_symbol,
            "market": market,
            "paths": paths,
            "path_count": len(paths),
            "risk_score": risk_score,
        }
        self.cache.cache.set(cache_key, result, ttl=1800)
        return result

    def _query_paths(
        self, from_symbol: str, to_symbol: str, market: str, max_depth: int
    ) -> List[List[Dict[str, Any]]]:
        """Cypher query for all simple paths up to max_depth."""
        query = """
            MATCH path = (a:Asset {symbol: $from, market: $market})
                      -[:CORRELATED_WITH|SUPPLY_CHAIN_OF|PAIRED_WITH|AFFECTS*1..%d]
                      ->(b:Asset {symbol: $to, market: $market})
            WITH path, nodes(path) AS ns, relationships(path) AS rs
            RETURN [n IN ns | {symbol: n.symbol, market: n.market, category: labels(n)[0]}] AS node_chain,
                   [r IN rs | {type: type(r), confidence: r.confidence}] AS rel_chain
            LIMIT 10
        """ % max_depth
        try:
            rows = run_cypher(query, {"from": from_symbol, "to": to_symbol, "market": market})
            paths: List[List[Dict[str, Any]]] = []
            for row in rows:
                node_chain = row.get("node_chain") or []
                rel_chain = row.get("rel_chain") or []
                # Zip into a readable step list
                steps = []
                for i, node in enumerate(node_chain):
                    steps.append({"node": node, "relation": rel_chain[i] if i < len(rel_chain) else None})
                paths.append(steps)
            return paths
        except Exception as e:
            logger.warning("Contagion path query failed: %s", e)
            return []

    def _score_paths(self, paths: List[List[Dict[str, Any]]]) -> float:
        """Heuristic risk score based on path count and depth."""
        if not paths:
            return 0.0
        # More short paths -> higher contagion risk
        avg_depth = sum(len(p) for p in paths) / len(paths)
        score = min(100.0, (len(paths) * 15.0) + max(0, (5 - avg_depth) * 5))
        return round(score, 2)

    # ------------------------------------------------------------------
    # Event impact tracing
    # ------------------------------------------------------------------
    def trace_event_impact(self, event_uid: str, max_depth: int = 3) -> Dict[str, Any]:
        """Trace how a single event ripples through the graph.

        Returns affected assets, intermediate events, and estimated impact radius.
        """
        cache_key = f"graph:event_impact:{event_uid}"
        cached = self.cache.cache.get(cache_key)
        if cached:
            return cached

        query = """
            MATCH path = (e:Event {uid: $uid})-[:AFFECTS|TRIGGERED_BY|IMPACTED_BY*1..%d]->(target)
            WITH path, nodes(path) AS ns, relationships(path) AS rs
            RETURN [n IN ns | {uid: n.uid, title: n.title, labels: labels(n)}] AS node_chain,
                   [r IN rs | {type: type(r)}] AS rel_chain,
                   length(path) AS depth
            LIMIT 20
        """ % max_depth
        try:
            rows = run_cypher(query, {"uid": event_uid})
        except Exception as e:
            logger.warning("Event impact trace failed: %s", e)
            rows = []

        affected_assets = []
        affected_events = []
        max_observed_depth = 0
        for row in rows:
            chain = row.get("node_chain") or []
            depth = row.get("depth", 0)
            max_observed_depth = max(max_observed_depth, depth)
            for node in chain:
                labels = node.get("labels") or []
                if "Asset" in labels:
                    affected_assets.append(node)
                elif "Event" in labels and node.get("uid") != event_uid:
                    affected_events.append(node)

        # Deduplicate by uid
        def _dedup(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            seen = set()
            out = []
            for item in items:
                uid = item.get("uid")
                if uid and uid not in seen:
                    seen.add(uid)
                    out.append(item)
            return out

        result = {
            "event_uid": event_uid,
            "affected_assets": _dedup(affected_assets),
            "affected_events": _dedup(affected_events),
            "max_depth": max_observed_depth,
            "impact_radius": min(100, max_observed_depth * 25 + len(affected_assets) * 5),
        }
        self.cache.cache.set(cache_key, result, ttl=1800)
        return result

    # ------------------------------------------------------------------
    # Cascade risk
    # ------------------------------------------------------------------
    def find_cascade_risk(self, symbol: str, market: str = "Crypto", depth: int = 2) -> Dict[str, Any]:
        """Assess cascade risk for a given asset (especially useful in crypto).

        Returns correlated assets, protocol dependencies, and an overall risk score.
        """
        cache_key = f"graph:cascade_risk:{market}:{symbol}"
        cached = self.cache.cache.get(cache_key)
        if cached:
            return cached

        correlated = self._query_correlated(symbol, market, depth)
        protocol_deps = self._query_protocol_deps(symbol, market)

        risk_score = self._score_cascade(symbol, correlated, protocol_deps)

        result = {
            "symbol": symbol,
            "market": market,
            "correlated_assets": correlated,
            "protocol_dependencies": protocol_deps,
            "correlation_count": len(correlated),
            "protocol_dependency_count": len(protocol_deps),
            "cascade_risk_score": risk_score,
            "risk_level": self._risk_label(risk_score),
        }
        self.cache.cache.set(cache_key, result, ttl=1800)
        return result

    def _query_correlated(self, symbol: str, market: str, depth: int) -> List[Dict[str, Any]]:
        query = """
            MATCH (a:Asset {symbol: $symbol, market: $market})
                  -[:CORRELATED_WITH|PAIRED_WITH*1..%d]-(related:Asset)
            RETURN DISTINCT related.symbol AS symbol,
                   related.market AS market,
                   labels(related)[0] AS category
            LIMIT 20
        """ % depth
        try:
            return run_cypher(query, {"symbol": symbol, "market": market}) or []
        except Exception as e:
            logger.warning("Cascade correlation query failed: %s", e)
            return []

    def _query_protocol_deps(self, symbol: str, market: str) -> List[Dict[str, Any]]:
        query = """
            MATCH (a:Asset {symbol: $symbol, market: $market})<-[:ISSUED|DEPLOYED_ON]-(p:Protocol)
            RETURN p.name AS name, p.category AS category, p.chain AS chain
            LIMIT 10
        """
        try:
            return run_cypher(query, {"symbol": symbol, "market": market}) or []
        except Exception as e:
            logger.warning("Protocol dependency query failed: %s", e)
            return []

    def _score_cascade(
        self, symbol: str, correlated: List[Dict[str, Any]], protocols: List[Dict[str, Any]]
    ) -> float:
        """Heuristic: more correlated assets + protocol deps = higher cascade risk."""
        score = len(correlated) * 3.0 + len(protocols) * 5.0
        # Boost for stablecoins (higher systemic importance)
        if symbol.upper() in ("USDT", "USDC", "DAI", "BUSD"):
            score += 30.0
        return round(min(100.0, score), 2)

    def _risk_label(self, score: float) -> str:
        if score >= 70:
            return "high"
        if score >= 40:
            return "medium"
        if score > 0:
            return "low"
        return "none"
