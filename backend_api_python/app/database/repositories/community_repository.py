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

    def list_pending_indicators(self, review_status: str = "pending", offset: int = 0, limit: int = 20):
        """按审核状态分页获取社区指标"""
        stmt = (
            select(CommunityIndicator)
            .where(CommunityIndicator.publish_to_community.is_(True))
            .where(CommunityIndicator.review_status == review_status)
            .order_by(CommunityIndicator.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def count_pending_indicators(self, review_status: str = "pending") -> int:
        """按审核状态统计社区指标数量"""
        from sqlalchemy import func
        stmt = (
            select(func.count())
            .select_from(CommunityIndicator)
            .where(CommunityIndicator.publish_to_community.is_(True))
            .where(CommunityIndicator.review_status == review_status)
        )
        return self.session.execute(stmt).scalar() or 0

    def get_review_stats(self) -> dict:
        """获取审核统计信息（pending/approved/rejected 数量）"""
        from sqlalchemy import func
        statuses = ["pending", "approved", "rejected"]
        stats = {}
        for status in statuses:
            stmt = (
                select(func.count())
                .select_from(CommunityIndicator)
                .where(CommunityIndicator.publish_to_community.is_(True))
                .where(CommunityIndicator.review_status == status)
            )
            stats[status] = self.session.execute(stmt).scalar() or 0
        # 总计（所有已发布到社区的）
        total_stmt = (
            select(func.count())
            .select_from(CommunityIndicator)
            .where(CommunityIndicator.publish_to_community.is_(True))
        )
        stats["total"] = self.session.execute(total_stmt).scalar() or 0
        return stats
