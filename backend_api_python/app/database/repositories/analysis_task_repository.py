"""Analysis task repository."""
from sqlalchemy import select, desc

from app.database.repositories.base import BaseRepository
from app.models.analysis_task import AnalysisTask


class AnalysisTaskRepository(BaseRepository):
    def get_by_id(self, task_id: int):
        return self.session.get(AnalysisTask, task_id)

    def list_by_user(
        self, user_id: int, market: str = "", symbol: str = "",
        limit: int = 20, offset: int = 0,
    ):
        stmt = select(AnalysisTask).where(AnalysisTask.user_id == user_id)
        if market:
            stmt = stmt.where(AnalysisTask.market == market)
        if symbol:
            stmt = stmt.where(AnalysisTask.symbol == symbol)
        stmt = stmt.order_by(desc(AnalysisTask.created_at)).offset(offset).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def create_task(self, **kwargs):
        task = AnalysisTask(**kwargs)
        self.add(task)
        self.flush()
        return task

    def update_task(self, task_id: int, **kwargs):
        task = self.get_by_id(task_id)
        if task:
            for k, v in kwargs.items():
                setattr(task, k, v)
            self.flush()
        return task

    def count_by_user(self, user_id: int) -> int:
        from sqlalchemy import func
        stmt = select(func.count()).where(AnalysisTask.user_id == user_id)
        return self.session.execute(stmt).scalar() or 0
