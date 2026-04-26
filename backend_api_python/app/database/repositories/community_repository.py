"""Community repository helpers."""
from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.models.community import CommunityIndicator


class CommunityRepository(BaseRepository):
    def get_indicator_by_id(self, indicator_id: int):
        return self.session.get(CommunityIndicator, indicator_id)

    def list_published_indicators(self, limit: int = 20):
        stmt = select(CommunityIndicator).where(CommunityIndicator.publish_to_community.is_(True)).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def list_market_indicators(self, limit: int = 50):
        stmt = (
            select(CommunityIndicator)
            .where(CommunityIndicator.publish_to_community.is_(True))
            .where((CommunityIndicator.review_status == "approved") | (CommunityIndicator.review_status.is_(None)))
            .order_by(CommunityIndicator.id.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())
