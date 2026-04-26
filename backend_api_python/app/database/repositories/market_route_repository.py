"""Market route repository helpers."""
from sqlalchemy import delete, select

from app.database.repositories.base import BaseRepository
from app.models.watchlist import Watchlist


class MarketRouteRepository(BaseRepository):
    def list_watchlist(self, user_id: int):
        stmt = select(Watchlist).where(Watchlist.user_id == user_id).order_by(Watchlist.id.desc())
        return list(self.session.execute(stmt).scalars())

    def get_watchlist_item(self, user_id: int, market: str, symbol: str):
        stmt = select(Watchlist).where(Watchlist.user_id == user_id, Watchlist.market == market, Watchlist.symbol == symbol)
        return self.session.execute(stmt).scalar_one_or_none()

    def upsert_watchlist_item(self, *, user_id: int, market: str, symbol: str, name: str):
        row = self.get_watchlist_item(user_id, market, symbol)
        if row is None:
            row = Watchlist(user_id=user_id, market=market, symbol=symbol, name=name)
            self.add(row)
        else:
            row.name = name
        self.flush()
        return row

    def delete_watchlist_by_symbol(self, user_id: int, symbol: str):
        self.session.execute(delete(Watchlist).where(Watchlist.user_id == user_id, Watchlist.symbol == symbol))
