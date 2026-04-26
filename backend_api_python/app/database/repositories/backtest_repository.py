"""Backtest repository helpers."""
from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.models.backtest import BacktestEquityPoint, BacktestResult, BacktestTrade


class BacktestRepository(BaseRepository):
    def get_run_by_id(self, run_id: int):
        return self.session.get(BacktestResult, run_id)

    def list_user_runs(self, user_id: int, limit: int = 20):
        stmt = select(BacktestResult).where(BacktestResult.user_id == user_id).order_by(BacktestResult.id.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def create_run(self, **kwargs):
        run = BacktestResult(**kwargs)
        self.add(run)
        self.flush()
        return run

    def add_trade(self, **kwargs):
        trade = BacktestTrade(**kwargs)
        self.add(trade)
        self.flush()
        return trade

    def add_equity_point(self, **kwargs):
        point = BacktestEquityPoint(**kwargs)
        self.add(point)
        self.flush()
        return point
