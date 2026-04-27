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

    def count_strategy_trades_by_user(self, user_id: int):
        from sqlalchemy import func, or_
        from app.models.strategy import StrategyTrading
        stmt = (
            select(func.count(StrategyTrade.id))
            .join(StrategyTrading, StrategyTrade.strategy_id == StrategyTrading.id)
            .where(
                StrategyTrade.user_id == user_id,
                StrategyTrading.user_id == user_id,
                or_(
                    func.lower(func.trim(StrategyTrading.strategy_mode)) != "bot",
                    StrategyTrading.strategy_mode == None,
                    StrategyTrading.strategy_mode == ""
                )
            )
        )
        return self.session.execute(stmt).scalar() or 0

    def list_strategy_trades_by_user(self, user_id: int, limit: int = 500):
        from sqlalchemy import desc, or_, func
        from app.models.strategy import StrategyTrading
        stmt = (
            select(StrategyTrade)
            .join(StrategyTrading, StrategyTrade.strategy_id == StrategyTrading.id)
            .where(
                StrategyTrade.user_id == user_id,
                StrategyTrading.user_id == user_id,
                or_(
                    func.lower(func.trim(StrategyTrading.strategy_mode)) != "bot",
                    StrategyTrading.strategy_mode == None,
                    StrategyTrading.strategy_mode == ""
                )
            )
            .order_by(desc(StrategyTrade.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())
