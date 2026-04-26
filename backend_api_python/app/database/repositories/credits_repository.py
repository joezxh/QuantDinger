"""Credits log repository."""
from sqlalchemy import select, desc

from app.database.repositories.base import BaseRepository
from app.models.credits import CreditsLog


class CreditsRepository(BaseRepository):
    def get_by_id(self, credits_id: int):
        return self.session.get(CreditsLog, credits_id)

    def list_by_user(self, user_id: int, limit: int = 50):
        stmt = (
            select(CreditsLog)
            .where(CreditsLog.user_id == user_id)
            .order_by(desc(CreditsLog.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_log(self, *, user_id, action, amount, balance_after, **kwargs):
        log = CreditsLog(
            user_id=user_id,
            action=action,
            amount=amount,
            balance_after=balance_after,
            **kwargs,
        )
        self.add(log)
        self.flush()
        return log
