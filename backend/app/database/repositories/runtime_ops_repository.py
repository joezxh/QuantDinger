"""Runtime log, analysis memory, and USDT payment repositories."""
from sqlalchemy import func, select

from app.database.repositories.base import BaseRepository
from app.models.analysis_task import AnalysisMemory
from app.models.membership import UsdtOrder
from app.models.notification import StrategyLog


class RuntimeOpsRepository(BaseRepository):
    def add_strategy_log(self, strategy_id: int, level: str, message: str):
        row = StrategyLog(strategy_id=strategy_id, level=level, message=message)
        self.add(row)
        self.flush()
        return row

    def create_analysis_memory(self, **kwargs):
        row = AnalysisMemory(**kwargs)
        self.add(row)
        self.flush()
        return row

    def list_recent_analysis_memory(self, market: str, symbol: str, days: int, limit: int):
        stmt = (
            select(AnalysisMemory)
            .where(AnalysisMemory.market == market, AnalysisMemory.symbol == symbol)
            .where(AnalysisMemory.created_at > func.now() - func.make_interval(days=days))
            .order_by(AnalysisMemory.created_at.desc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def get_usdt_order(self, order_id: int, user_id: int):
        stmt = select(UsdtOrder).where(UsdtOrder.id == order_id, UsdtOrder.user_id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_max_usdt_address_index(self, chain: str):
        stmt = select(func.max(UsdtOrder.address_index)).where(UsdtOrder.chain == chain)
        return self.session.execute(stmt).scalar_one_or_none()

    def create_usdt_order(self, **kwargs):
        row = UsdtOrder(**kwargs)
        self.add(row)
        self.flush()
        return row
