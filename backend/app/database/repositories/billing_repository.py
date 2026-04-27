"""Billing repository helpers."""
from sqlalchemy import select

from app.database.repositories.base import BaseRepository
from app.models.billing import BillingRecord
from app.models.membership import MembershipOrder
from app.models.user import User


class BillingRepository(BaseRepository):
    def get_user_credits(self, user_id: int):
        user = self.session.get(User, user_id)
        return getattr(user, "credits", 0) if user else 0

    def get_user_vip_expires_at(self, user_id: int):
        user = self.session.get(User, user_id)
        return getattr(user, "vip_expires_at", None) if user else None

    def add_billing_record(self, **kwargs):
        record = BillingRecord(**kwargs)
        self.add(record)
        self.flush()
        return record

    def list_user_billing_records(self, user_id: int, limit: int = 20):
        stmt = select(BillingRecord).where(BillingRecord.user_id == user_id).order_by(BillingRecord.id.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def get_user_billing_info(self, user_id: int) -> dict:
        """获取用户计费信息"""
        user = self.session.get(User, user_id)
        if not user:
            return {}
        return {
            'credits': float(user.credits or 0),
            'vip_expires_at': str(user.vip_expires_at) if user.vip_expires_at else None,
            'is_vip': bool(user.vip_expires_at)
        }

    def create_membership_order(self, user_id: int, plan: str, price_usd: float, status: str = "paid") -> MembershipOrder:
        """创建会员订单记录"""
        order = MembershipOrder(
            user_id=user_id,
            plan=plan,
            price_usd=price_usd,
            status=status,
        )
        self.add(order)
        self.flush()
        self.refresh(order)
        return order
