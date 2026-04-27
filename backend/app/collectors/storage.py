"""Collector storage for structured persistence."""
from typing import Iterable, List, Optional

from app.database.repositories.market_repository import MarketRepository
from app.database.session import get_session


class CollectorStorage:
    def _save_via_repository(self, repo: MarketRepository, item):
        return repo.save_collection_record(
            source=item.source,
            data_type=item.data_type,
            market=item.market,
            symbol=item.symbol,
            content_hash=item.content_hash,
        )

    def save_item(self, item):
        with get_session() as session:
            repo = MarketRepository(session)
            return self._save_via_repository(repo, item)

    def save_items(self, items: Iterable) -> List:
        with get_session() as session:
            repo = MarketRepository(session)
            return [self._save_via_repository(repo, item) for item in items]

    def get_by_content_hash(self, content_hash: str):
        with get_session() as session:
            repo = MarketRepository(session)
            return repo.get_collection_record_by_hash(content_hash)

    def save_collection_record(self, item):
        return self.save_item(item)

    def save_collection_records(self, items: Iterable) -> List:
        return self.save_items(items)

    def exists(self, content_hash: str) -> bool:
        with get_session() as session:
            repo = MarketRepository(session)
            return repo.exists_by_content_hash(content_hash)
