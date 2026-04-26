"""Market symbol repository."""
from sqlalchemy import select, desc

from app.database.repositories.base import BaseRepository
from app.models.market_symbol import MarketSymbol


class MarketSymbolRepository(BaseRepository):
    def get_by_id(self, symbol_id: int):
        return self.session.get(MarketSymbol, symbol_id)

    def list_by_market(self, market: str, is_active: int = 1, is_hot: int = None):
        stmt = (
            select(MarketSymbol)
            .where(
                MarketSymbol.market == market,
                MarketSymbol.is_active == is_active,
            )
            .order_by(desc(MarketSymbol.sort_order))
        )
        if is_hot is not None:
            stmt = stmt.where(MarketSymbol.is_hot == is_hot)
        return list(self.session.execute(stmt).scalars())

    def get_by_symbol(self, market: str, symbol: str):
        stmt = (
            select(MarketSymbol)
            .where(
                MarketSymbol.market == market,
                MarketSymbol.symbol == symbol,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_hot_by_market(self, market: str, limit: int = 20):
        stmt = (
            select(MarketSymbol)
            .where(
                MarketSymbol.market == market,
                MarketSymbol.is_hot == 1,
                MarketSymbol.is_active == 1,
            )
            .order_by(desc(MarketSymbol.sort_order))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_symbol(self, **kwargs):
        symbol = MarketSymbol(**kwargs)
        self.add(symbol)
        self.flush()
        return symbol

    def update_symbol(self, symbol_id: int, **kwargs):
        symbol = self.get_by_id(symbol_id)
        if symbol:
            for k, v in kwargs.items():
                setattr(symbol, k, v)
            self.flush()
        return symbol
