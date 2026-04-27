"""Analysis memory repository."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, desc, func

from app.database.repositories.base import BaseRepository
from app.models.analysis_task import AnalysisMemory


class AnalysisMemoryRepository(BaseRepository):
    def get_by_id(self, memory_id: int):
        return self.session.get(AnalysisMemory, memory_id)

    def list_by_symbol(
        self, market: str, symbol: str, limit: int = 20, offset: int = 0,
    ):
        stmt = (
            select(AnalysisMemory)
            .where(
                AnalysisMemory.market == market,
                AnalysisMemory.symbol == symbol,
            )
            .order_by(desc(AnalysisMemory.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def list_by_user(
        self, user_id: int, limit: int = 20, offset: int = 0,
    ):
        stmt = (
            select(AnalysisMemory)
            .where(AnalysisMemory.user_id == user_id)
            .order_by(desc(AnalysisMemory.created_at))
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_memory(self, **kwargs):
        memory = AnalysisMemory(**kwargs)
        self.add(memory)
        self.flush()
        return memory

    def update_feedback(self, memory_id: int, *, was_correct: bool, actual_return_pct=None, user_feedback=None):
        memory = self.get_by_id(memory_id)
        if memory:
            memory.was_correct = was_correct
            if actual_return_pct is not None:
                memory.actual_return_pct = actual_return_pct
            if user_feedback is not None:
                memory.user_feedback = user_feedback
            self.flush()
        return memory

    def get_accuracy_stats(self, market: str, symbol: str):
        stmt = (
            select(
                func.count().label("total"),
                func.sum(func.cast(AnalysisMemory.was_correct, type_=func.integer())).label("correct"),
            )
            .where(
                AnalysisMemory.market == market,
                AnalysisMemory.symbol == symbol,
                AnalysisMemory.was_correct.isnot(None),
            )
        )
        row = self.session.execute(stmt).one()
        total = row.total or 0
        correct = row.correct or 0
        accuracy = (correct / total * 100) if total > 0 else 0.0
        return {"total": total, "correct": correct, "accuracy": accuracy}

    def list_for_calibration(self, market: str, lookback_days: int = 30):
        """Fetch validated analysis memory rows suitable for AI calibration."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        stmt = (
            select(AnalysisMemory)
            .where(
                AnalysisMemory.market == market,
                AnalysisMemory.validated_at.isnot(None),
                AnalysisMemory.actual_return_pct.isnot(None),
                AnalysisMemory.consensus_score.isnot(None),
                AnalysisMemory.created_at > cutoff,
            )
        )
        return list(self.session.execute(stmt).scalars())
