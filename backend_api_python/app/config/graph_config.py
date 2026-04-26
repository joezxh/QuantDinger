"""Graph/Neo4j configuration with fine-grained feature toggles."""
import os


class GraphConfig:
    """Centralized graph-related configuration."""

    # Main switch
    GRAPHITI_ENABLED: bool = os.getenv("GRAPHITI_ENABLED", "false").lower() == "true"

    # Fine-grained switches (effective only when GRAPHITI_ENABLED is True)
    GRAPHITI_NARRATIVE_EXTRACTION: bool = (
        os.getenv("GRAPHITI_NARRATIVE", "false").lower() == "true"
    )
    GRAPHITI_CONFLICT_RESOLUTION: bool = (
        os.getenv("GRAPHITI_CONFLICT", "false").lower() == "true"
    )
    GRAPHITI_GRAPHRAG_SEARCH: bool = (
        os.getenv("GRAPHITI_GRAPHRAG", "false").lower() == "true"
    )

    # Quality thresholds (trigger Phase-2 enablement conditions)
    MIN_EPISODE_COUNT: int = int(os.getenv("GRAPH_MIN_EPISODES", "1000"))
    MIN_ENTITY_COUNT: int = int(os.getenv("GRAPH_MIN_ENTITIES", "500"))
    MIN_RELATION_COUNT: int = int(os.getenv("GRAPH_MIN_RELATIONS", "2000"))

    # LLM settings for Graphiti
    GRAPHITI_LLM_MODEL: str = os.getenv("GRAPHITI_LLM_MODEL", "gpt-4o-mini")
    GRAPHITI_IMPORTANCE_THRESHOLD: float = float(
        os.getenv("GRAPHITI_IMPORTANCE_THRESHOLD", "0.65")
    )

    # Neo4j connection
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "quantdinger")

    # Cache TTLs
    GRAPH_CACHE_TTL: int = int(os.getenv("GRAPH_CACHE_TTL", "600"))
    GRAPH_CONTEXT_TTL: int = int(os.getenv("GRAPH_CONTEXT_TTL", "300"))
