"""Polymarket route repository helpers."""
from sqlalchemy import func, select

from app.database.repositories.base import BaseRepository
from app.models.analysis_task import AnalysisTask


class PolymarketRouteRepository(BaseRepository):
    def count_user_history(self, user_id: int):
        stmt = select(func.count(AnalysisTask.id)).where(AnalysisTask.user_id == user_id, AnalysisTask.market == "Polymarket")
        return int(self.session.execute(stmt).scalar() or 0)

    def list_user_history(self, user_id: int, limit: int, offset: int):
        stmt = (
            select(AnalysisTask)
            .where(AnalysisTask.user_id == user_id, AnalysisTask.market == "Polymarket")
            .order_by(AnalysisTask.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.execute(stmt).scalars())
