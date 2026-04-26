"""Order repository."""
from typing import Optional

from sqlalchemy import select, desc

from app.database.repositories.base import BaseRepository
from app.models.order import PendingOrder, QuickTrade


class OrderRepository(BaseRepository):
    def get_pending_by_id(self, order_id: int):
        return self.session.get(PendingOrder, order_id)

    def list_pending_by_user(self, user_id: int, limit: int = 50):
        stmt = (
            select(PendingOrder)
            .where(PendingOrder.user_id == user_id)
            .order_by(desc(PendingOrder.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def list_pending_by_status(self, status: str, limit: int = 50):
        stmt = (
            select(PendingOrder)
            .where(PendingOrder.status == status)
            .order_by(PendingOrder.priority.asc())
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_pending_order(self, **kwargs):
        order = PendingOrder(**kwargs)
        self.add(order)
        self.flush()
        return order

    def update_pending_status(self, order_id: int, status: str, **kwargs):
        order = self.get_pending_by_id(order_id)
        if order:
            order.status = status
            for k, v in kwargs.items():
                setattr(order, k, v)
            self.flush()
        return order

    def get_quick_trade_by_id(self, trade_id: int):
        return self.session.get(QuickTrade, trade_id)

    def list_quick_trades_by_user(self, user_id: int, limit: int = 50):
        stmt = (
            select(QuickTrade)
            .where(QuickTrade.user_id == user_id)
            .order_by(desc(QuickTrade.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_quick_trade(self, **kwargs):
        trade = QuickTrade(**kwargs)
        self.add(trade)
        self.flush()
        return trade

    def update_quick_trade(self, trade_id: int, **kwargs):
        trade = self.get_quick_trade_by_id(trade_id)
        if trade:
            for k, v in kwargs.items():
                setattr(trade, k, v)
            self.flush()
        return trade

    # ── trading_executor dedup helpers ──

    def find_last_pending_order(
        self,
        strategy_id: int,
        symbol: str,
        signal_type: str,
        signal_ts: Optional[int] = None,
    ) -> Optional[dict]:
        """Find the most recent pending order for dedup checks.

        Returns a dict with id, status, created_at or None.
        """
        stmt = (
            select(PendingOrder.id, PendingOrder.status, PendingOrder.created_at)
            .where(
                PendingOrder.strategy_id == strategy_id,
                PendingOrder.symbol == symbol,
                PendingOrder.signal_type == signal_type,
            )
            .order_by(PendingOrder.id.desc())
            .limit(1)
        )
        if signal_ts is not None:
            stmt = stmt.where(PendingOrder.signal_ts == signal_ts)
        row = self.session.execute(stmt).first()
        if not row:
            return None
        return {'id': row.id, 'status': row.status, 'created_at': int(row.created_at.timestamp()) if row.created_at else 0}

    def create_pending_order_full(self, **kwargs):
        """Create a pending order with all fields. Delegates to create_pending_order."""
        return self.create_pending_order(**kwargs)
