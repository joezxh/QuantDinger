"""Graph pipeline that bridges collected items to graph jobs."""
import asyncio
from typing import Iterable, List, Optional

from app.collectors.episode_builder import EpisodeBuilder
from app.collectors.storage import CollectorStorage
from app.database.repositories.graph_repository import GraphRepository
from app.database.session import get_session
from app.graph.graphiti_gateway import GraphitiGateway
from app.utils.cache import CacheManager
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GraphPipeline:
    def __init__(self, episode_builder=None, graphiti_gateway=None, cache_manager=None, collector_storage=None):
        self.episode_builder = episode_builder or EpisodeBuilder()
        self.graphiti_gateway = graphiti_gateway or GraphitiGateway()
        self.cache = cache_manager or CacheManager()
        self.collector_storage = collector_storage or CollectorStorage()

    def process_item(self, item):
        collection_record = self._save_collection_record(item)
        episode = self.episode_builder.build(item)
        if not episode:
            return {"status": "skipped", "collection_record_id": getattr(collection_record, "id", None)}

        if self._should_skip_by_dedup(episode):
            return {
                "status": "dedup_skipped",
                "dedup_key": episode.dedup_key,
                "collection_record_id": getattr(collection_record, "id", None),
            }

        with get_session() as session:
            repo = GraphRepository(session)
            existing_episode = repo.get_episode_by_dedup_key(episode.dedup_key)
            if existing_episode:
                return {
                    "status": "episode_exists",
                    "episode_id": existing_episode.id,
                    "collection_record_id": getattr(collection_record, "id", None),
                }

            episode_record = repo.save_episode(
                episode_type=episode.episode_type,
                market_domain=episode.market_domain,
                title=episode.title,
                source=episode.source,
                source_ref=episode.source_ref,
                dedup_key=episode.dedup_key,
                importance_score=episode.importance_score,
                event_time=episode.event_time,
                observed_time=episode.observed_time,
            )
            job = repo.create_graph_job(episode_id=episode_record.id, job_type="graphiti_ingest")
            self._bind_collection_entity_ref(repo, collection_record)

            try:
                result = self._dispatch_episode(episode)
                repo.mark_episode_status(episode_record.id, "completed")
                repo.update_graph_job(job.id, "completed")
                self._mark_dedup(episode)
                return {
                    "status": "completed",
                    "episode_id": episode_record.id,
                    "job_id": job.id,
                    "collection_record_id": getattr(collection_record, "id", None),
                    "dispatch_result": result,
                }
            except Exception as e:
                logger.error(f"Graph pipeline dispatch failed: {e}", exc_info=True)
                repo.mark_episode_status(episode_record.id, "failed", str(e))
                repo.update_graph_job(job.id, "failed", str(e))
                return {
                    "status": "failed",
                    "episode_id": episode_record.id,
                    "job_id": job.id,
                    "collection_record_id": getattr(collection_record, "id", None),
                    "error": str(e),
                }

    def process_items(self, items: Iterable) -> List[dict]:
        return [self.process_item(item) for item in items]

    def _save_collection_record(self, item):
        try:
            return self.collector_storage.save_collection_record(item)
        except Exception:
            return None

    def _bind_collection_entity_ref(self, repo: GraphRepository, collection_record: Optional[object]):
        if collection_record is None:
            return None
        return repo.upsert_entity_ref(
            entity_uid=f"collection:{collection_record.id}",
            entity_type="collection_record",
            source_table="qd_collection_records",
            source_pk=str(collection_record.id),
        )

    def _should_skip_by_dedup(self, episode) -> bool:
        if not episode.dedup_key:
            return False
        return self.cache.get(f"graph:episode:dedup:{episode.dedup_key}") is not None

    def _mark_dedup(self, episode):
        if episode.dedup_key:
            self.cache.set(f"graph:episode:dedup:{episode.dedup_key}", {"seen": True}, ttl=86400)

    def _dispatch_episode(self, episode):
        return asyncio.run(self.graphiti_gateway.add_episode(episode))
