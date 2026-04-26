"""Strategy trade repository."""
from datetime import date, timedelta

from sqlalchemy import select, func

from app.database.repositories.base import BaseRepository
from app.models.trading import StrategyTrade


class TradeRepository(BaseRepository):
    def get_realized_pnl(self, strategy_id: int) -> float:
        """Calculate total realized PnL (profit - commission) for a strategy."""
        stmt = select(
            func.coalesce(func.sum(func.coalesce(StrategyTrade.profit, 0) -
                                  func.coalesce(StrategyTrade.commission, 0)), 0)
        ).where(
            StrategyTrade.strategy_id == strategy_id,
        )
        result = self.session.execute(stmt).scalar()
        return float(result) if result is not None else 0.0

    def get_daily_pnl(self, strategy_id: int) -> float:
        """Calculate today's realized PnL for a strategy."""
        today = date.today()
        stmt = select(
            func.coalesce(func.sum(func.coalesce(StrategyTrade.profit, 0) -
                                  func.coalesce(StrategyTrade.commission, 0)), 0)
        ).where(
            StrategyTrade.strategy_id == strategy_id,
            func.date(StrategyTrade.created_at) == today,
        )
        result = self.session.execute(stmt).scalar()
        return float(result) if result is not None else 0.0

    def create_trade(self, **kwargs):
        """Record a trade."""
        trade = StrategyTrade(**kwargs)
        self.add(trade)
        self.flush()
        return trade
