"""Watchlist repository."""
from sqlalchemy import select, desc

from app.database.repositories.base import BaseRepository
from app.models.watchlist import Watchlist


class WatchlistRepository(BaseRepository):
    def get_by_id(self, watchlist_id: int):
        return self.session.get(Watchlist, watchlist_id)

    def list_by_user(self, user_id: int, limit: int = 100):
        stmt = (
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .order_by(desc(Watchlist.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def get_by_symbol(self, user_id: int, market: str, symbol: str):
        stmt = (
            select(Watchlist)
            .where(
                Watchlist.user_id == user_id,
                Watchlist.market == market,
                Watchlist.symbol == symbol,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def add_item(self, *, user_id, market, symbol, name=""):
        existing = self.get_by_symbol(user_id, market, symbol)
        if existing:
            return existing
        item = Watchlist(user_id=user_id, market=market, symbol=symbol, name=name)
        self.add(item)
        self.flush()
        return item

    def remove_item(self, user_id: int, market: str, symbol: str):
        item = self.get_by_symbol(user_id, market, symbol)
        if item:
            self.session.delete(item)
            self.flush()
            return True
        return False

    def exists(self, user_id: int, market: str, symbol: str) -> bool:
        return self.get_by_symbol(user_id, market, symbol) is not None
