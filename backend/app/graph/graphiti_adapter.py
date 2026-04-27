"""Graphiti adapter for QuantDinger — wraps Graphiti with graceful degradation.

Uses the local ``graphiti_core`` copy and project-specific configuration.
"""
from __future__ import annotations

import os
from typing import Any, Iterable, List

from app.config.graph_config import GraphConfig
from app.utils.logger import get_logger

logger = get_logger(__name__)


class QuantDingerGraphiti:
    """QuantDinger-specific Graphiti wrapper.

    Lazy-initialises the underlying ``Graphiti`` instance only when
    ``GRAPHITI_ENABLED=true``.  All methods degrade gracefully when
    the feature is disabled or the back-end is unreachable.
    """

    _instance: Any | None = None

    def __init__(self, config: GraphConfig | None = None):
        self.config = config or GraphConfig()

    def _get_instance(self) -> Any | None:
        if self._instance is not None:
            return self._instance

        if not self.config.GRAPHITI_ENABLED:
            return None

        try:
            from graphiti_core import Graphiti

            self._instance = Graphiti(
                uri=self.config.NEO4J_URI,
                user=self.config.NEO4J_USER,
                password=self.config.NEO4J_PASSWORD,
            )
            logger.info("Graphiti instance initialised.")
        except Exception as exc:
            logger.warning(f"Graphiti initialisation failed: {exc}")
            self._instance = None

        return self._instance

    # ------------------------------------------------------------------
    # Episode ingestion
    # ------------------------------------------------------------------
    async def add_episode(self, episode: Any) -> dict:
        instance = self._get_instance()
        if instance is None:
            return {"status": "disabled"}

        try:
            return await instance.add_episode(
                name=getattr(episode, "title", "unknown"),
                content=getattr(episode, "content", ""),
                source_description=getattr(episode, "source", ""),
                reference_time=getattr(
                    episode, "event_time", getattr(episode, "observed_time", None)
                ),
            )
        except Exception as exc:
            logger.warning(f"Graphiti add_episode failed: {exc}")
            return {"status": "error", "error": str(exc)}

    async def add_episodes(self, episodes: Iterable[Any]) -> List[dict]:
        results: List[dict] = []
        for ep in episodes:
            results.append(await self.add_episode(ep))
        return results

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    async def search(self, query: str, group_id: str | None = None) -> List[Any]:
        instance = self._get_instance()
        if instance is None:
            return []

        try:
            if hasattr(instance, "search"):
                return await instance.search(query=query, group_id=group_id)
        except Exception as exc:
            logger.warning(f"Graphiti search failed: {exc}")
        return []

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def is_enabled(self) -> bool:
        return self.config.GRAPHITI_ENABLED

    def is_ready_for_phase2(self) -> bool:
        """Return *True* only if all fine-grained switches may be turned on.

        This is a lightweight check; for the full readiness report with
        counts see :class:`app.graph.quality_monitor.GraphQualityMonitor`.
        """
        return self.config.GRAPHITI_ENABLED
