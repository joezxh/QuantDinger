"""Graph data quality monitoring — readiness checks for Phase-2 enablement."""
from typing import Dict, List

from app.graph.connection import run_cypher
from app.config.graph_config import GraphConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GraphQualityMonitor:
    """Monitor graph data volume and quality to decide when Graphiti
    advanced features (narrative extraction, conflict resolution,
    GraphRAG) can be safely enabled.
    """

    def __init__(self, config: GraphConfig | None = None):
        self.config = config or GraphConfig()

    def _count_episodes(self) -> int:
        result = run_cypher("MATCH (e:Episode) RETURN count(e) AS cnt")
        return result[0]["cnt"] if result else 0

    def _count_entities(self) -> int:
        result = run_cypher("MATCH (n:Entity) RETURN count(n) AS cnt")
        return result[0]["cnt"] if result else 0

    def _count_relations(self) -> int:
        result = run_cypher("MATCH ()-[r:RELATES_TO]->() RETURN count(r) AS cnt")
        return result[0]["cnt"] if result else 0

    def _avg_confidence(self) -> float:
        result = run_cypher(
            "MATCH (e:Episode) RETURN avg(e.confidence) AS avg_conf"
        )
        return result[0]["avg_conf"] or 0.0 if result else 0.0

    def check_readiness(self) -> Dict[str, object]:
        """Check whether graph data has reached the quality bar for
        enabling Graphiti advanced features.

        Returns a dict with counts, averages, and an overall ``is_ready`` flag.
        """
        episode_count = self._count_episodes()
        entity_count = self._count_entities()
        relation_count = self._count_relations()
        min_confidence_avg = self._avg_confidence()

        checks: List[bool] = [
            episode_count >= self.config.MIN_EPISODE_COUNT,
            entity_count >= self.config.MIN_ENTITY_COUNT,
            relation_count >= self.config.MIN_RELATION_COUNT,
        ]

        is_ready = all(checks)

        if is_ready:
            logger.info(
                "Graph quality thresholds met — Phase-2 features can be enabled."
            )
        else:
            logger.info(
                "Graph quality below thresholds — keeping Phase-1 (Cypher-only)."
            )

        return {
            "episode_count": episode_count,
            "entity_count": entity_count,
            "relation_count": relation_count,
            "min_confidence_avg": round(min_confidence_avg, 4),
            "thresholds": {
                "min_episodes": self.config.MIN_EPISODE_COUNT,
                "min_entities": self.config.MIN_ENTITY_COUNT,
                "min_relations": self.config.MIN_RELATION_COUNT,
            },
            "is_ready": is_ready,
        }
