"""Neo4j connection helpers with graceful fallback."""
import os
from typing import Any, Dict, List

from app.utils.logger import get_logger

logger = get_logger(__name__)

_driver = None


def get_driver():
    global _driver
    if _driver is not None:
        return _driver

    try:
        from neo4j import GraphDatabase

        _driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://neo4j:7687"),
            auth=(
                os.getenv("NEO4J_USER", "neo4j"),
                os.getenv("NEO4J_PASSWORD", "quantdinger"),
            ),
        )
        return _driver
    except Exception as e:
        logger.warning(f"Neo4j driver unavailable: {e}")
        _driver = False
        return None


def run_cypher(query: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    driver = get_driver()
    if not driver:
        return []

    try:
        with driver.session() as session:
            return session.run(query, params or {}).data()
    except Exception as e:
        logger.warning(f"Cypher execution failed: {e}")
        return []
