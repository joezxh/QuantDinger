"""Portfolio and pending order repository helpers."""
from sqlalchemy import delete, func, select

from app.database.repositories.base import BaseRepository
from app.models.order import PendingOrder
from app.models.position import ManualPosition, StrategyPosition, PositionMonitor


class PortfolioRepository(BaseRepository):
    def list_manual_positions(self, user_id: int, position_ids=None):
        stmt = select(ManualPosition).where(ManualPosition.user_id == user_id)
        if position_ids:
            stmt = stmt.where(ManualPosition.id.in_(position_ids))
        return list(self.session.execute(stmt).scalars())

    def list_strategy_positions(self, strategy_id=None):
        stmt = select(StrategyPosition)
        if strategy_id is not None:
            stmt = stmt.where(StrategyPosition.strategy_id == strategy_id)
        return list(self.session.execute(stmt).scalars())

    def list_strategy_positions_by_user(self, user_id: int):
        from sqlalchemy import or_, desc
        from app.models.strategy import StrategyTrading
        stmt = (
            select(StrategyPosition)
            .join(StrategyTrading, StrategyPosition.strategy_id == StrategyTrading.id)
            .where(
                StrategyPosition.user_id == user_id,
                StrategyTrading.user_id == user_id,
                or_(
                    func.lower(func.trim(StrategyTrading.strategy_mode)) != "bot",
                    StrategyTrading.strategy_mode == None,
                    StrategyTrading.strategy_mode == ""
                )
            )
            .order_by(desc(StrategyPosition.updated_at))
        )
        return list(self.session.execute(stmt).scalars())

    def update_strategy_position_snapshot(self, position_id: int, *, current_price: float, unrealized_pnl: float, pnl_percent: float):
        row = self.session.get(StrategyPosition, position_id)
        if not row:
            return None
        row.current_price = current_price
        row.unrealized_pnl = unrealized_pnl
        row.pnl_percent = pnl_percent
        row.updated_at = func.now()
        self.flush()
        return row

    def list_monitors(self, user_id: int):
        stmt = select(PositionMonitor).where(PositionMonitor.user_id == user_id).order_by(PositionMonitor.id.desc())
        return list(self.session.execute(stmt).scalars())


class PendingOrderRepository(BaseRepository):
    def list_pending_orders(self, limit: int = 50):
        stmt = select(PendingOrder).where(PendingOrder.status == "pending").order_by(PendingOrder.id.asc()).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def mark_processing(self, order_id: int):
        row = self.session.get(PendingOrder, order_id)
        if not row or row.status != "pending":
            return False
        row.status = "processing"
        self.flush()
        return True

    def mark_failed(self, order_id: int, error: str):
        row = self.session.get(PendingOrder, order_id)
        if not row:
            return None
        row.status = "failed"
        row.payload_json = error
        self.flush()
        return row

    def delete_order(self, order_id: int):
        self.session.execute(delete(PendingOrder).where(PendingOrder.id == order_id))
