"""Cross-domain entity bridging — align entities across stock, crypto and
polymarket domains so that graph queries can follow relationships that span
markets.

Examples of bridges:
- Apple Inc. (stock ticker AAPL)  ↔  Apple token on crypto exchanges
- BlackRock (institutional holder) ↔  Polymarket whale wallet
- Tesla (TSLA)                     ↔  Elon-Musk-related prediction markets
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from app.graph.connection import run_cypher
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class BridgeRule:
    """Hard-coded bridge rule for known cross-domain aliases."""

    source_label: str
    source_key: str
    source_value: str
    target_label: str
    target_key: str
    target_value: str
    relation_type: str = "ALIAS_OF"
    reason: str = ""


# ---------------------------------------------------------------------------
# Seed rules — maintained by operators.  Expand as new mappings are discovered.
# ---------------------------------------------------------------------------
_DEFAULT_RULES: Tuple[BridgeRule, ...] = (
    # Example: Apple stock ↔ Apple token (hypothetical)
    # BridgeRule(
    #     source_label="Company",
    #     source_key="ticker",
    #     source_value="AAPL",
    #     target_label="Asset",
    #     target_key="symbol",
    #     target_value="AAPL-USDT",
    #     relation_type="ALIAS_OF",
    #     reason="Same underlying company",
    # ),
)


class EntityBridge:
    """Manage cross-domain entity alignment.

    Two alignment mechanisms are supported:

    1. **Rule-based (deterministic)** — ``seed_rules`` are applied verbatim.
    2. **Heuristic (fuzzy)** — name / symbol similarity is used to propose
       candidate bridges that must be reviewed before creation.
    """

    def __init__(self, seed_rules: Optional[List[BridgeRule]] = None):
        self.seed_rules = list(seed_rules or _DEFAULT_RULES)
        self._similarity_threshold = float(
            os.getenv("ENTITY_BRIDGE_SIMILARITY_THRESHOLD", "0.85")
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_seed_rules(self) -> int:
        """Create MERGE relationships for every hard-coded seed rule.

        Returns the number of relationships created (or verified present).
        """
        created = 0
        for rule in self.seed_rules:
            if self._merge_bridge_relation(rule):
                created += 1
        logger.info(f"EntityBridge: applied {created}/{len(self.seed_rules)} seed rules")
        return created

    def find_candidates(
        self,
        source_label: str,
        target_label: str,
        *,
        key_prop: str = "name",
        limit: int = 50,
    ) -> List[Dict]:
        """Heuristic candidate discovery based on exact or near-exact name match.

        Uses a simple Cypher query that looks for nodes in two different labels
        whose ``key_prop`` values share a high Jaccard similarity on word
        tokens.  This is intentionally lightweight; heavy NLP matching can be
        plugged in later.
        """
        query = """
            MATCH (a:%(source_label)s), (b:%(target_label)s)
            WHERE a.%(key_prop)s IS NOT NULL AND b.%(key_prop)s IS NOT NULL
            WITH a, b,
                 apoc.text.jaroWinklerDistance(
                     toLower(a.%(key_prop)s), toLower(b.%(key_prop)s)
                 ) AS sim
            WHERE sim >= $threshold
            RETURN {
                source: {label: "%(source_label)s", key: a.%(key_prop)s, uid: a.uid},
                target: {label: "%(target_label)s", key: b.%(key_prop)s, uid: b.uid},
                similarity: sim
            } AS candidate
            ORDER BY sim DESC
            LIMIT $limit
        """ % {"source_label": source_label, "target_label": target_label, "key_prop": key_prop}

        try:
            rows = run_cypher(
                query,
                {"threshold": self._similarity_threshold, "limit": limit},
            )
            return [r["candidate"] for r in rows] if rows else []
        except Exception as exc:
            # apoc may not be installed — degrade gracefully
            logger.warning(
                f"EntityBridge heuristic search failed ({exc}); "
                "falling back to exact-token overlap."
            )
            return self._find_candidates_fallback(
                source_label, target_label, key_prop=key_prop, limit=limit
            )

    def create_bridge(
        self,
        source_label: str,
        source_uid: str,
        target_label: str,
        target_uid: str,
        relation_type: str = "CROSS_REFERENCED",
        reason: str = "",
    ) -> bool:
        """Create a single cross-domain bridge relationship (idempotent)."""
        query = """
            MATCH (a:%(source_label)s {uid: $source_uid})
            MATCH (b:%(target_label)s {uid: $target_uid})
            MERGE (a)-[r:%(relation_type)s {reason: $reason}]->(b)
            ON CREATE SET r.created_at = datetime()
            RETURN count(r) AS cnt
        """ % {"source_label": source_label, "target_label": target_label, "relation_type": relation_type}

        try:
            result = run_cypher(query, {
                "source_uid": source_uid,
                "target_uid": target_uid,
                "reason": reason or "manual",
            })
            return bool(result and result[0].get("cnt", 0) > 0)
        except Exception as exc:
            logger.error(f"Failed to create bridge: {exc}")
            return False

    def get_bridged_entities(
        self,
        label: str,
        uid: str,
        *,
        relation_type: Optional[str] = None,
        direction: str = "both",
    ) -> List[Dict]:
        """Return all entities on the other side of a bridge from the given node.

        Parameters
        ----------
        label : str
            Node label (e.g. ``Company``).
        uid : str
            Unique id property of the node.
        relation_type : str, optional
            Filter by relationship type (default: any bridge relation).
        direction : {"out", "in", "both"}
            Which direction to traverse.
        """
        rel_filter = (f":{relation_type}" if relation_type else "")
        if direction == "out":
            pattern = f"(a:{label} {{uid: $uid}})-[r{rel_filter}]->(b)"
        elif direction == "in":
            pattern = f"(a:{label} {{uid: $uid}})<-[r{rel_filter}]-(b)"
        else:
            pattern = f"(a:{label} {{uid: $uid}})-[r{rel_filter}]-(b)"

        query = f"""
            MATCH {pattern}
            RETURN distinct b AS node, type(r) AS rel_type, r.reason AS reason
        """
        try:
            rows = run_cypher(query, {"uid": uid})
            return [
                {
                    "node": r["node"],
                    "relation_type": r["rel_type"],
                    "reason": r["reason"],
                }
                for r in (rows or [])
            ]
        except Exception as exc:
            logger.error(f"get_bridged_entities failed: {exc}")
            return []

    def delete_bridge(
        self,
        source_label: str,
        source_uid: str,
        target_label: str,
        target_uid: str,
        relation_type: Optional[str] = None,
    ) -> bool:
        """Delete a specific bridge relationship."""
        rel_filter = (f"r:{relation_type}" if relation_type else "r")
        query = """
            MATCH (a:%(source_label)s {uid: $source_uid})
                  -[%s]->
                  (b:%(target_label)s {uid: $target_uid})
            DELETE r
            RETURN count(r) AS cnt
        """ % rel_filter % {"source_label": source_label, "target_label": target_label}

        try:
            result = run_cypher(query, {"source_uid": source_uid, "target_uid": target_uid})
            return bool(result and result[0].get("cnt", 0) > 0)
        except Exception as exc:
            logger.error(f"Failed to delete bridge: {exc}")
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _merge_bridge_relation(self, rule: BridgeRule) -> bool:
        query = """
            MATCH (a:%(source_label)s {%(source_key)s: $source_value})
            MATCH (b:%(target_label)s {%(target_key)s: $target_value})
            MERGE (a)-[r:%(relation_type)s {reason: $reason}]->(b)
            ON CREATE SET r.created_at = datetime()
            RETURN count(r) AS cnt
        """ % {
            "source_label": rule.source_label,
            "source_key": rule.source_key,
            "target_label": rule.target_label,
            "target_key": rule.target_key,
            "relation_type": rule.relation_type,
        }
        try:
            result = run_cypher(
                query,
                {
                    "source_value": rule.source_value,
                    "target_value": rule.target_value,
                    "reason": rule.reason or "seed_rule",
                },
            )
            return bool(result and result[0].get("cnt", 0) > 0)
        except Exception as exc:
            logger.warning(f"Seed rule failed ({rule}): {exc}")
            return False

    def _find_candidates_fallback(
        self,
        source_label: str,
        target_label: str,
        *,
        key_prop: str = "name",
        limit: int = 50,
    ) -> List[Dict]:
        """Fallback when APOC is unavailable — uses exact substring overlap."""
        query = """
            MATCH (a:%(source_label)s), (b:%(target_label)s)
            WHERE a.%(key_prop)s IS NOT NULL AND b.%(key_prop)s IS NOT NULL
              AND toLower(a.%(key_prop)s) CONTAINS toLower(b.%(key_prop)s)
                 OR toLower(b.%(key_prop)s) CONTAINS toLower(a.%(key_prop)s)
            RETURN {
                source: {label: "%(source_label)s", key: a.%(key_prop)s, uid: a.uid},
                target: {label: "%(target_label)s", key: b.%(key_prop)s, uid: b.uid},
                similarity: 0.9
            } AS candidate
            LIMIT $limit
        """ % {"source_label": source_label, "target_label": target_label, "key_prop": key_prop}

        try:
            rows = run_cypher(query, {"limit": limit})
            return [r["candidate"] for r in rows] if rows else []
        except Exception as exc:
            logger.error(f"Fallback candidate search failed: {exc}")
            return []


# ---------------------------------------------------------------------------
# Convenience singleton
# ---------------------------------------------------------------------------
_bridge_instance: Optional[EntityBridge] = None


def get_entity_bridge() -> EntityBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = EntityBridge()
    return _bridge_instance
