"""Billing Service - 统一计费服务"""
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple

from app.database.repositories.billing_repository import BillingRepository
from app.database.session import get_session
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
                return BillingRepository(session).get_user_billing_info(user_id)
        except Exception as e:
            logger.error(f"get_user_billing_info failed: {e}")
            return {}

    def get_membership_plans(self) -> list:
        """获取会员套餐列表"""
        # TODO: 从数据库或配置中读取套餐信息
        return [
            {
                'id': 'free',
                'name': '免费版',
                'price': 0,
                'credits': 100,
                'features': ['基础分析', '10次AI查询/月'],
                'is_popular': False
            },
            {
                'id': 'basic',
                'name': '基础版',
                'price': 99,
                'credits': 1000,
                'features': ['所有分析功能', '100次AI查询/月', '技术指标库'],
                'is_popular': True
            },
            {
                'id': 'pro',
                'name': '专业版',
                'price': 299,
                'credits': 5000,
                'features': ['所有功能', '无限AI查询', '回测功能', '实时数据', '优先支持'],
                'is_popular': False
            },
            {
                'id': 'enterprise',
                'name': '企业版',
                'price': 999,
                'credits': 20000,
                'features': ['所有专业版功能', 'API访问', '私有部署', '专属客服'],
                'is_popular': False
            }
        ]


def get_billing_service() -> BillingService:
    return BillingService()