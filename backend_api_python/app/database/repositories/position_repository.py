"""Position repository."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, desc, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database.repositories.base import BaseRepository
from app.models.position import ManualPosition, PositionAlert, PositionMonitor, StrategyPosition


class PositionRepository(BaseRepository):
    def get_strategy_position_by_id(self, position_id: int):
        return self.session.get(StrategyPosition, position_id)

    def list_strategy_positions_by_user(self, user_id: int, limit: int = 50):
        stmt = (
            select(StrategyPosition)
            .where(StrategyPosition.user_id == user_id)
            .order_by(desc(StrategyPosition.updated_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def list_strategy_positions_by_strategy(self, strategy_id: int):
        stmt = select(StrategyPosition).where(
            StrategyPosition.strategy_id == strategy_id,
        )
        return list(self.session.execute(stmt).scalars())

    def create_strategy_position(self, **kwargs):
        position = StrategyPosition(**kwargs)
        self.add(position)
        self.flush()
        return position

    def update_strategy_position(self, position_id: int, **kwargs):
        position = self.get_strategy_position_by_id(position_id)
        if position:
            for k, v in kwargs.items():
                setattr(position, k, v)
            self.flush()
        return position

    def get_manual_position_by_id(self, position_id: int):
        return self.session.get(ManualPosition, position_id)

    def list_manual_positions_by_user(self, user_id: int):
        stmt = (
            select(ManualPosition)
            .where(ManualPosition.user_id == user_id)
            .order_by(desc(ManualPosition.created_at))
        )
        return list(self.session.execute(stmt).scalars())

    def create_manual_position(self, **kwargs):
        position = ManualPosition(**kwargs)
        self.add(position)
        self.flush()
        return position

    def update_manual_position(self, position_id: int, **kwargs):
        position = self.get_manual_position_by_id(position_id)
        if position:
            for k, v in kwargs.items():
                setattr(position, k, v)
            self.flush()
        return position

    def delete_manual_position(self, position_id: int):
        position = self.get_manual_position_by_id(position_id)
        if position:
            self.session.delete(position)
            self.flush()
            return True
        return False

    def get_alert_by_id(self, alert_id: int):
        return self.session.get(PositionAlert, alert_id)

    def list_alerts_by_user(self, user_id: int, is_active: int = None):
        stmt = select(PositionAlert).where(PositionAlert.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(PositionAlert.is_active == is_active)
        stmt = stmt.order_by(desc(PositionAlert.created_at))
        return list(self.session.execute(stmt).scalars())

    def create_alert(self, **kwargs):
        alert = PositionAlert(**kwargs)
        self.add(alert)
        self.flush()
        return alert

    def update_alert(self, alert_id: int, **kwargs):
        alert = self.get_alert_by_id(alert_id)
        if alert:
            for k, v in kwargs.items():
                setattr(alert, k, v)
            self.flush()
        return alert

    def get_monitor_by_id(self, monitor_id: int):
        return self.session.get(PositionMonitor, monitor_id)

    def list_monitors_by_user(self, user_id: int, is_active: int = None):
        stmt = select(PositionMonitor).where(PositionMonitor.user_id == user_id)
        if is_active is not None:
            stmt = stmt.where(PositionMonitor.is_active == is_active)
        stmt = stmt.order_by(desc(PositionMonitor.created_at))
        return list(self.session.execute(stmt).scalars())

    def create_monitor(self, **kwargs):
        monitor = PositionMonitor(**kwargs)
        self.add(monitor)
        self.flush()
        return monitor

    def update_monitor(self, monitor_id: int, **kwargs):
        monitor = self.get_monitor_by_id(monitor_id)
        if monitor:
            for k, v in kwargs.items():
                setattr(monitor, k, v)
            self.flush()
        return monitor

    # ── trading_executor helpers ──

    def delete_position(self, strategy_id: int, symbol: str, side: str) -> bool:
        """Close position by strategy, symbol, side."""
        stmt = select(StrategyPosition).where(
            StrategyPosition.strategy_id == strategy_id,
            StrategyPosition.symbol == symbol,
            StrategyPosition.side == side,
        )
        positions = list(self.session.execute(stmt).scalars())
        for pos in positions:
            self.session.delete(pos)
        self.flush()
        return len(positions) > 0

    def upsert_position(
        self,
        strategy_id: int,
        user_id: int,
        symbol: str,
        side: str,
        size: Decimal,
        entry_price: Decimal,
        current_price: Decimal,
        highest_price: Decimal = Decimal('0'),
        lowest_price: Decimal = Decimal('0'),
    ):
        """Upsert strategy position (INSERT ON CONFLICT DO UPDATE)."""
        now = datetime.utcnow()
        stmt = pg_insert(StrategyPosition).values(
            user_id=user_id,
            strategy_id=strategy_id,
            symbol=symbol,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=current_price,
            highest_price=highest_price,
            lowest_price=lowest_price,
            updated_at=now,
        ).on_conflict_do_update(
            constraint='qd_strategy_positions_strategy_id_symbol_side_key',
            set_={
                'size': size,
                'entry_price': entry_price,
                'current_price': current_price,
                'highest_price': func.case(
                    (highest_price > 0, highest_price),
                    else_=StrategyPosition.highest_price,
                ),
                'lowest_price': func.case(
                    (lowest_price > 0, lowest_price),
                    else_=StrategyPosition.lowest_price,
                ),
                'updated_at': now,
            },
        )
        self.session.execute(stmt)
        self.flush()

    def update_positions_price(self, strategy_id: int, symbol: str, current_price: Decimal):
        """Update current_price for all positions of a given strategy/symbol."""
        stmt = select(StrategyPosition).where(
            StrategyPosition.strategy_id == strategy_id,
            StrategyPosition.symbol == symbol,
        )
        positions = list(self.session.execute(stmt).scalars())
        for pos in positions:
            pos.current_price = current_price
        self.flush()
