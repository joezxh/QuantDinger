"""Live trading repository helpers."""
from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.models.exchange import ExchangeCredential
from app.models.position import StrategyPosition
from app.models.strategy import StrategyTrading
from app.models.trading import StrategyTrade


class LiveTradingRepository(BaseRepository):
    def get_strategy_config(self, strategy_id: int):
        row = self.session.get(StrategyTrading, strategy_id)
        return row

    def get_exchange_credential(self, credential_id: int, user_id: int):
        stmt = select(ExchangeCredential).where(ExchangeCredential.id == credential_id, ExchangeCredential.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def add_trade(self, **kwargs):
        row = StrategyTrade(**kwargs)
        self.add(row)
        self.flush()
        return row

    def get_position(self, strategy_id: int, symbol: str, side: str):
        stmt = select(StrategyPosition).where(
            StrategyPosition.strategy_id == strategy_id,
            StrategyPosition.symbol == symbol,
            StrategyPosition.side == side,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def delete_position(self, strategy_id: int, symbol: str, side: str):
        row = self.get_position(strategy_id, symbol, side)
        if row:
            self.session.delete(row)
            self.flush()

    def upsert_position(self, **kwargs):
        row = self.get_position(kwargs["strategy_id"], kwargs["symbol"], kwargs["side"])
        if row is None:
            row = StrategyPosition(**kwargs)
            self.add(row)
        else:
            for key, value in kwargs.items():
                setattr(row, key, value)
        self.flush()
        return row
