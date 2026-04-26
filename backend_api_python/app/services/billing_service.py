"""Billing Service - 统一计费服务"""
import os
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple

from app.database.repositories.billing_repository import BillingRepository
from app.database.session import get_session
from app.models.credits import CreditsLog
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)

BILLING_CONFIG_PREFIX = 'BILLING_'
DEFAULT_BILLING_CONFIG = {
    'enabled': False,
    'cost_ai_analysis': 10,
    'cost_ai_code_gen': 30,
    'cost_polymarket_deep_analysis': 15,
}
FEATURE_NAMES = {
    'ai_analysis': 'AI Analysis',
    'ai_code_gen': 'AI Code Generation',
    'polymarket_deep_analysis': 'Polymarket Deep Analysis',
}


class BillingService:
    def __init__(self):
        self._config_cache = None
        self._config_cache_time = 0
        self._cache_ttl = 60

    def get_billing_config(self) -> Dict[str, Any]:
        now = time.time()
        if self._config_cache and (now - self._config_cache_time) < self._cache_ttl:
            return self._config_cache

        config = {}
        for key, default_value in DEFAULT_BILLING_CONFIG.items():
            env_key = f'{BILLING_CONFIG_PREFIX}{key.upper()}'
            value = os.getenv(env_key)
            if value is None or value == '':
                config[key] = default_value
            elif isinstance(default_value, bool):
                config[key] = str(value).lower() in ('true', '1', 'yes')
            elif isinstance(default_value, int):
                try:
                    config[key] = int(value)
                except (ValueError, TypeError):
                    config[key] = default_value
            else:
                config[key] = value

        self._config_cache = config
        self._config_cache_time = now
        return config

    def clear_config_cache(self):
        self._config_cache = None
        self._config_cache_time = 0

    def is_billing_enabled(self) -> bool:
        return self.get_billing_config().get('enabled', False)

    def get_feature_cost(self, feature: str) -> int:
        config = self.get_billing_config()
        return config.get(f'cost_{feature}', 0)

    def get_user_credits(self, user_id: int) -> Decimal:
        try:
            with get_session() as session:
                credits = BillingRepository(session).get_user_credits(user_id)
                return Decimal(str(credits or 0))
        except Exception as e:
            logger.error(f"get_user_credits failed: {e}")
            return Decimal('0')

    def get_user_vip_status(self, user_id: int) -> Tuple[bool, Optional[datetime]]:
        try:
            with get_session() as session:
                expires_at = BillingRepository(session).get_user_vip_expires_at(user_id)
                if not expires_at:
                    return False, None
                if isinstance(expires_at, str):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                return expires_at > now, expires_at
        except Exception as e:
            logger.error(f"get_user_vip_status failed: {e}")
            return False, None

    def add_billing_record(self, **kwargs):
        try:
            with get_session() as session:
                return BillingRepository(session).add_billing_record(**kwargs)
        except Exception as e:
            logger.error(f"add_billing_record failed: {e}")
            return None

    def list_user_billing_records(self, user_id: int, limit: int = 20):
        try:
            with get_session() as session:
                return BillingRepository(session).list_user_billing_records(user_id, limit=limit)
        except Exception as e:
            logger.error(f"list_user_billing_records failed: {e}")
            return []

    def get_user_billing_info(self, user_id: int) -> dict:
        """获取用户计费信息"""
        try:
            with get_session() as session:
                info = BillingRepository(session).get_user_billing_info(user_id)
                info['billing_enabled'] = self.is_billing_enabled()
                return info
        except Exception as e:
            logger.error(f"get_user_billing_info failed: {e}")
            return {'credits': 0, 'vip_expires_at': None, 'is_vip': False, 'billing_enabled': False}

    def get_credits_log(self, user_id: int, page: int = 1, page_size: int = 20) -> dict:
        """获取用户积分变动日志（分页）"""
        try:
            with get_session() as session:
                from sqlalchemy import func
                query = session.query(CreditsLog).filter(CreditsLog.user_id == user_id)
                total = query.count()
                items = query.order_by(CreditsLog.id.desc()).offset(
                    (page - 1) * page_size
                ).limit(page_size).all()
                return {
                    "items": [
                        {
                            "id": item.id,
                            "action": item.action,
                            "amount": float(item.amount),
                            "balance_after": float(item.balance_after),
                            "feature": item.feature,
                            "reference_id": item.reference_id,
                            "remark": item.remark,
                            "operator_id": item.operator_id,
                            "created_at": item.created_at.isoformat() if item.created_at else None,
                        }
                        for item in items
                    ],
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                }
        except Exception as e:
            logger.error(f"get_credits_log failed: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

    def add_credits(self, user_id: int, amount, action: str, remark: str = '', reference_id: str = '', operator_id: int = None) -> bool:
        """增加/扣除用户积分，并记录日志"""
        try:
            with get_session() as session:
                user = session.get(User, user_id)
                if not user:
                    logger.error(f"add_credits: user {user_id} not found")
                    return False
                current_credits = Decimal(str(user.credits or 0))
                delta = Decimal(str(amount))
                new_balance = current_credits + delta
                if new_balance < 0:
                    logger.warning(f"add_credits: insufficient credits for user {user_id}")
                    return False
                user.credits = new_balance
                log = CreditsLog(
                    user_id=user_id,
                    action=action,
                    amount=delta,
                    balance_after=new_balance,
                    reference_id=reference_id,
                    remark=remark,
                    operator_id=operator_id,
                )
                session.add(log)
                session.flush()
                return True
        except Exception as e:
            logger.error(f"add_credits failed: {e}")
            return False

    def get_membership_plans(self) -> dict:
        """获取会员套餐列表（兼容前端字段格式）"""
        def _f(key, default):
            try:
                return float(os.getenv(key, default) or default)
            except (ValueError, TypeError):
                return default

        def _i(key, default):
            try:
                return int(os.getenv(key, default) or default)
            except (ValueError, TypeError):
                return default

        return {
            "monthly": {
                "plan": "monthly",
                "price_usd": _f("MEMBERSHIP_MONTHLY_PRICE_USD", 19.9),
                "credits_once": _i("MEMBERSHIP_MONTHLY_CREDITS", 500),
                "duration_days": 30,
            },
            "yearly": {
                "plan": "yearly",
                "price_usd": _f("MEMBERSHIP_YEARLY_PRICE_USD", 199.0),
                "credits_once": _i("MEMBERSHIP_YEARLY_CREDITS", 8000),
                "duration_days": 365,
            },
            "lifetime": {
                "plan": "lifetime",
                "price_usd": _f("MEMBERSHIP_LIFETIME_PRICE_USD", 499.0),
                "credits_monthly": _i("MEMBERSHIP_LIFETIME_MONTHLY_CREDITS", 800),
            },
        }

    def purchase_membership(self, user_id: int, plan: str) -> Tuple[bool, str, Dict[str, Any]]:
        """购买会员套餐（Mock支付：立即开通）"""
        plan = (plan or "").strip().lower()
        plans = self.get_membership_plans()
        if plan not in plans:
            return False, "invalid_plan", {}

        try:
            with get_session() as session:
                from app.database.repositories.billing_repository import BillingRepository
                repo = BillingRepository(session)
                now = datetime.now(timezone.utc)

                # 获取当前用户VIP过期时间，支持叠加
                user = session.get(User, user_id)
                if not user:
                    return False, "user_not_found", {}

                current_expires = user.vip_expires_at
                if current_expires and current_expires.tzinfo is None:
                    current_expires = current_expires.replace(tzinfo=timezone.utc)
                base_time = current_expires if (current_expires and current_expires > now) else now

                vip_expires_at = None
                vip_plan = plan
                vip_is_lifetime = False

                if plan in ("monthly", "yearly"):
                    days = int(plans[plan].get("duration_days") or (30 if plan == "monthly" else 365))
                    vip_expires_at = base_time + timedelta(days=days)
                else:
                    # lifetime: 设置很长的过期时间 + 标记lifetime
                    vip_expires_at = now + timedelta(days=365 * 100)
                    vip_is_lifetime = True

                # 创建订单记录
                price_usd = float(plans[plan].get("price_usd") or 0)
                order = repo.create_membership_order(
                    user_id=user_id,
                    plan=plan,
                    price_usd=price_usd,
                    status="paid",
                )
                order_ref = str(order.id)

                # 更新用户VIP字段
                user.vip_expires_at = vip_expires_at
                user.vip_plan = vip_plan
                user.vip_is_lifetime = vip_is_lifetime
                session.flush()

                # 获取当前积分余额用于日志记录
                current_credits = Decimal(str(user.credits or 0))

                # 发放积分
                if plan in ("monthly", "yearly"):
                    credits_once = int(plans[plan].get("credits_once") or 0)
                    if credits_once > 0:
                        new_balance = current_credits + Decimal(str(credits_once))
                        user.credits = new_balance
                        log = CreditsLog(
                            user_id=user_id,
                            action="membership_bonus",
                            amount=Decimal(str(credits_once)),
                            balance_after=new_balance,
                            reference_id=order_ref,
                            remark=f"Membership bonus ({plan})",
                        )
                        session.add(log)
                        current_credits = new_balance
                        session.flush()
                else:
                    # Lifetime: 首次发放月度积分
                    monthly_credits = int(plans["lifetime"].get("credits_monthly") or 0)
                    if monthly_credits > 0:
                        new_balance = current_credits + Decimal(str(monthly_credits))
                        user.credits = new_balance
                        log = CreditsLog(
                            user_id=user_id,
                            action="membership_monthly",
                            amount=Decimal(str(monthly_credits)),
                            balance_after=new_balance,
                            reference_id=order_ref,
                            remark="Lifetime membership monthly credits",
                        )
                        session.add(log)
                        current_credits = new_balance
                        user.vip_monthly_credits_last_grant = now
                        session.flush()

                # VIP购买日志记录（审计）
                audit_log = CreditsLog(
                    user_id=user_id,
                    action="membership_purchase",
                    amount=Decimal("0"),
                    balance_after=current_credits,
                    reference_id=order_ref,
                    remark=f"Membership purchased: {plan}",
                )
                session.add(audit_log)
                session.commit()

            return True, "success", {
                "order_id": order.id,
                "plan": plan,
                "vip_expires_at": vip_expires_at.isoformat() if vip_expires_at else None,
            }
        except Exception as e:
            logger.error(f"purchase_membership failed: {e}", exc_info=True)
            return False, f"error:{str(e)}", {}


def get_billing_service() -> BillingService:
    return BillingService()