"""Portfolio repository helpers."""
from sqlalchemy import delete, select

from app.database.repositories.base import BaseRepository
from app.models.position import ManualPosition


class PortfolioRouteRepository(BaseRepository):
    def list_positions(self, user_id: int):
        stmt = select(ManualPosition).where(ManualPosition.user_id == user_id).order_by(ManualPosition.id.desc())
        return list(self.session.execute(stmt).scalars())

    def create_or_replace_position(self, *, user_id: int, market: str, symbol: str, group_name: str, **kwargs):
        self.session.execute(delete(ManualPosition).where(
            ManualPosition.user_id == user_id,
            ManualPosition.market == market,
            ManualPosition.symbol == symbol,
            ManualPosition.group_name == group_name,
        ))
        row = ManualPosition(user_id=user_id, market=market, symbol=symbol, group_name=group_name, **kwargs)
        self.add(row)
        self.flush()
        return row

    def get_position(self, position_id: int, user_id: int):
        stmt = select(ManualPosition).where(ManualPosition.id == position_id, ManualPosition.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def update_position(self, position_id: int, user_id: int, **kwargs):
        row = self.get_position(position_id, user_id)
        if not row:
            return None
        for key, value in kwargs.items():
            setattr(row, key, value)
        self.flush()
        return row

    def delete_position(self, position_id: int, user_id: int):
        self.session.execute(delete(ManualPosition).where(ManualPosition.id == position_id, ManualPosition.user_id == user_id))
