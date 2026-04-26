"""Graphiti gateway with graceful degradation and helpers."""
import os
from typing import Any, Iterable, List

from app.utils.logger import get_logger

logger = get_logger(__name__)


class GraphitiGateway:
    def __init__(self, client: Any = None):
        self.client = client
        self.enabled = os.getenv("GRAPHITI_ENABLED", "false").lower() == "true"

    async def add_episode(self, episode):
        if not self.enabled:
            return {"status": "disabled"}
        if self.client is None:
            logger.warning("Graphiti client is not configured")
            return {"status": "no_client"}

        try:
            return await self.client.add_episode(
                name=episode.title,
                content=episode.content,
                source_description=episode.source,
                reference_time=episode.event_time or episode.observed_time,
            )
        except Exception as e:
            logger.warning(f"Graphiti add_episode failed: {e}")
            return {"status": "error", "error": str(e)}

    async def add_episodes(self, episodes: Iterable):
        results: List[dict] = []
        for episode in episodes:
            results.append(await self.add_episode(episode))
        return results

    async def search(self, query: str, group_id: str | None = None):
        if not self.enabled or self.client is None:
            return []
        try:
            if hasattr(self.client, "search"):
                return await self.client.search(query=query, group_id=group_id)
        except Exception as e:
            logger.warning(f"Graphiti search failed: {e}")
        return []
