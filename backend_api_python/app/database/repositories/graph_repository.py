"""Repository for graph-related persistence."""
from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.models.graph_domain import CompanyNarrativeFeature, CryptoNarrativeFeature, PolymarketMarketFeature
from app.models.graph_meta import (
    GraphEntityRef,
    GraphEpisode,
    GraphFeatureDaily,
    GraphJob,
    GraphRelationSnapshot,
)


class GraphRepository(BaseRepository):
    def save_episode(
        self,
        *,
        episode_type: str,
        market_domain: str,
        title: Optional[str],
        source: str,
        source_ref: Optional[str],
        dedup_key: Optional[str],
        importance_score: float,
        event_time,
        observed_time,
        status: str = "pending",
    ) -> GraphEpisode:
        episode = GraphEpisode(
            episode_type=episode_type,
            market_domain=market_domain,
            title=title,
            source=source,
            source_ref=source_ref,
            dedup_key=dedup_key,
            importance_score=importance_score,
            event_time=event_time,
            observed_time=observed_time,
            status=status,
        )
        self.add(episode)
        self.flush()
        return episode

    def create_episode(self, **kwargs) -> GraphEpisode:
        return self.save_episode(**kwargs)

    def get_episode_by_dedup_key(self, dedup_key: Optional[str]):
        if not dedup_key:
            return None
        stmt = select(GraphEpisode).where(GraphEpisode.dedup_key == dedup_key)
        return self.session.execute(stmt).scalar_one_or_none()

    def mark_episode_status(self, episode_id: int, status: str, error_message: Optional[str] = None):
        episode = self.session.get(GraphEpisode, episode_id)
        if episode:
            episode.status = status
            episode.error_message = error_message
            self.flush()
        return episode

    def update_episode_status(self, episode_id: int, status: str, error_message: Optional[str] = None):
        return self.mark_episode_status(episode_id, status, error_message)

    def create_graph_job(self, *, episode_id: Optional[int], job_type: str, status: str = "pending") -> GraphJob:
        job = GraphJob(
            episode_id=episode_id,
            job_type=job_type,
            status=status,
            started_at=datetime.utcnow(),
        )
        self.add(job)
        self.flush()
        return job

    def create_job(self, *, episode_id: Optional[int], job_type: str, status: str = "pending") -> GraphJob:
        return self.create_graph_job(episode_id=episode_id, job_type=job_type, status=status)

    def update_graph_job(self, job_id: int, status: str, error_message: Optional[str] = None):
        job = self.session.get(GraphJob, job_id)
        if job:
            job.status = status
            job.error_message = error_message
            if status in {"completed", "failed"}:
                job.finished_at = datetime.utcnow()
            self.flush()
        return job

    def update_job_status(self, job_id: int, status: str, error_message: Optional[str] = None):
        return self.update_graph_job(job_id, status, error_message)

    def upsert_entity_ref(self, *, entity_uid: str, entity_type: str, source_table: str, source_pk: str):
        stmt = select(GraphEntityRef).where(
            GraphEntityRef.entity_type == entity_type,
            GraphEntityRef.source_table == source_table,
            GraphEntityRef.source_pk == source_pk,
        )
        existing = self.session.execute(stmt).scalar_one_or_none()
        if existing:
            existing.entity_uid = entity_uid
            self.flush()
            return existing

        ref = GraphEntityRef(
            entity_uid=entity_uid,
            entity_type=entity_type,
            source_table=source_table,
            source_pk=source_pk,
        )
        self.add(ref)
        self.flush()
        return ref

    def insert_feature_batch(self, features: Iterable[GraphFeatureDaily]):
        self.add_all(list(features))
        self.flush()

    def insert_company_narrative_features(self, features: Iterable[CompanyNarrativeFeature]):
        self.add_all(list(features))
        self.flush()

    def insert_crypto_narrative_features(self, features: Iterable[CryptoNarrativeFeature]):
        self.add_all(list(features))
        self.flush()

    def insert_polymarket_market_features(self, features: Iterable[PolymarketMarketFeature]):
        self.add_all(list(features))
        self.flush()

    def get_features_by_symbol(self, market: str, symbol: str, start_date=None, end_date=None):
        stmt = select(GraphFeatureDaily).where(
            GraphFeatureDaily.market == market,
            GraphFeatureDaily.symbol == symbol,
        )
        if start_date is not None:
            stmt = stmt.where(GraphFeatureDaily.trade_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(GraphFeatureDaily.trade_date <= end_date)
        stmt = stmt.order_by(GraphFeatureDaily.trade_date.desc())
        return list(self.session.execute(stmt).scalars())

    def add_relation_snapshot(self, snapshot: GraphRelationSnapshot):
        self.add(snapshot)
        self.flush()
        return snapshot
