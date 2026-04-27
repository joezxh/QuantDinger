"""Repository for market and collection persistence."""
from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.models.collection import CollectionRecord


class MarketRepository(BaseRepository):
    def create_collection_record(self, *, source, data_type, market, symbol, content_hash):
        existing = self.get_collection_record_by_hash(content_hash)
        if existing:
            return existing

        record = CollectionRecord(
            source=source,
            data_type=data_type,
            market=market,
            symbol=symbol,
            content_hash=content_hash,
        )
        self.add(record)
        self.flush()
        return record

    def save_collection_record(self, **kwargs):
        return self.create_collection_record(**kwargs)

    def exists_by_content_hash(self, content_hash: str) -> bool:
        stmt = select(CollectionRecord.id).where(CollectionRecord.content_hash == content_hash)
        return self.session.execute(stmt).first() is not None

    def get_collection_record_by_hash(self, content_hash: str):
        stmt = select(CollectionRecord).where(CollectionRecord.content_hash == content_hash)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_market_types(self):
        from app.models.market_symbol import MarketSymbol
        stmt = select(MarketSymbol.market).where(MarketSymbol.is_active == 1).distinct()
        return list(self.session.execute(stmt).scalars())
