"""Membership order repository."""
from sqlalchemy import select, desc

from app.database.repositories.base import BaseRepository
from app.models.membership import MembershipOrder, UsdtOrder


class MembershipRepository(BaseRepository):
    def get_order_by_id(self, order_id: int):
        return self.session.get(MembershipOrder, order_id)

    def list_orders_by_user(self, user_id: int, limit: int = 50):
        stmt = (
            select(MembershipOrder)
            .where(MembershipOrder.user_id == user_id)
            .order_by(desc(MembershipOrder.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_order(self, *, user_id, plan, price_usd=0, status="paid", **kwargs):
        order = MembershipOrder(
            user_id=user_id,
            plan=plan,
            price_usd=price_usd,
            status=status,
            **kwargs,
        )
        self.add(order)
        self.flush()
        return order

    def get_usdt_order_by_id(self, order_id: int):
        return self.session.get(UsdtOrder, order_id)

    def list_usdt_orders_by_user(self, user_id: int, limit: int = 50):
        stmt = (
            select(UsdtOrder)
            .where(UsdtOrder.user_id == user_id)
            .order_by(desc(UsdtOrder.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_usdt_order(self, *, user_id, plan, chain="TRC20", amount_usdt=0, **kwargs):
        order = UsdtOrder(
            user_id=user_id,
            plan=plan,
            chain=chain,
            amount_usdt=amount_usdt,
            **kwargs,
        )
        self.add(order)
        self.flush()
        return order

    def update_usdt_order_status(self, order_id: int, status: str, **kwargs):
        order = self.get_usdt_order_by_id(order_id)
        if order:
            order.status = status
            for k, v in kwargs.items():
                setattr(order, k, v)
            self.flush()
        return order
