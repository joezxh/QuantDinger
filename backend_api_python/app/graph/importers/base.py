"""Base graph importer with batching and idempotency."""
from __future__ import annotations

from typing import Any, Dict, List

from app.graph.connection import run_cypher
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BaseGraphImporter:
    """Base class for domain-specific graph importers.

    Subclasses should override :meth:`import_batch` to read from Postgres
    and write to Neo4j via Cypher MERGE statements.
    """

    def __init__(self, batch_size: int = 500):
        self.batch_size = batch_size

    def _run_merge_nodes(self, label: str, key_prop: str, nodes: List[Dict[str, Any]]) -> int:
        """Merge a batch of nodes into Neo4j.

        Uses UNWIND + MERGE for efficient batch insertion.
        """
        if not nodes:
            return 0
        query = f"""
            UNWIND $nodes AS node
            MERGE (n:{label} {{{key_prop}: node.{key_prop}}})
            SET n += node
            RETURN count(n) AS cnt
        """
        try:
            result = run_cypher(query, {"nodes": nodes})
            return result[0].get("cnt", 0) if result else 0
        except Exception as e:
            logger.warning("Merge %s nodes failed: %s", label, e)
            return 0

    def _run_merge_relationships(
        self,
        rel_type: str,
        from_label: str,
        from_key: str,
        to_label: str,
        to_key: str,
        rels: List[Dict[str, Any]],
    ) -> int:
        """Merge a batch of relationships into Neo4j."""
        if not rels:
            return 0
        query = f"""
            UNWIND $rels AS rel
            MATCH (a:{from_label} {{{from_key}: rel.from_id}})
            MATCH (b:{to_label} {{{to_key}: rel.to_id}})
            MERGE (a)-[r:{rel_type}]->(b)
            SET r += rel.props
            RETURN count(r) AS cnt
        """
        try:
            result = run_cypher(query, {"rels": rels})
            return result[0].get("cnt", 0) if result else 0
        except Exception as e:
            logger.warning("Merge %s relationships failed: %s", rel_type, e)
            return 0

    def import_batch(self) -> Dict[str, int]:
        """Run one import batch.  Return counters."""
        raise NotImplementedError
