"""
Community Service - 指标社区服务

处理指标市场、购买、评论等功能。
"""
import json
import time
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple

from app.database.repositories.community_repository import CommunityRepository
from app.database.session import get_session
from app.services.billing_service import get_billing_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CommunityService:
    """指标社区服务类"""

    def __init__(self):
        self.billing = get_billing_service()

    def _indicator_to_market_item(self, indicator, user_id: int = None) -> Dict[str, Any]:
        return {
            'id': indicator.id,
            'name': indicator.name,
            'description': (indicator.description or '')[:200],
            'pricing_type': indicator.pricing_type or 'free',
            'price': float(indicator.price or 0),
            'vip_free': bool(getattr(indicator, 'vip_free', False)),
            'preview_image': indicator.preview_image or '',
            'purchase_count': getattr(indicator, 'purchase_count', 0) or 0,
            'avg_rating': float(getattr(indicator, 'avg_rating', 0) or 0),
            'rating_count': getattr(indicator, 'rating_count', 0) or 0,
            'view_count': getattr(indicator, 'view_count', 0) or 0,
            'created_at': indicator.created_at.isoformat() if indicator.created_at else None,
            'author': {
                'id': indicator.user_id,
                'username': None,
                'nickname': None,
                'avatar': '/avatar2.jpg',
            },
            'is_purchased': False,
            'is_own': indicator.user_id == user_id,
        }

    def get_market_indicators(
        self,
        page: int = 1,
        page_size: int = 12,
        keyword: str = None,
        pricing_type: str = None,
        sort_by: str = 'newest',
        user_id: int = None,
    ) -> Dict[str, Any]:
        try:
            with get_session() as session:
                indicators = CommunityRepository(session).list_market_indicators(limit=max(page_size * page, 20))

            if keyword and keyword.strip():
                search = keyword.strip().lower()
                indicators = [
                    item for item in indicators
                    if search in (item.name or '').lower() or search in (item.description or '').lower()
                ]

            if pricing_type == 'free':
                indicators = [item for item in indicators if (item.pricing_type == 'free' or float(item.price or 0) <= 0)]
            elif pricing_type == 'paid':
                indicators = [item for item in indicators if (item.pricing_type != 'free' and float(item.price or 0) > 0)]

            if sort_by == 'hot':
                indicators.sort(key=lambda x: ((x.purchase_count or 0), (x.view_count or 0)), reverse=True)
            elif sort_by == 'price_asc':
                indicators.sort(key=lambda x: (float(x.price or 0), -(x.id or 0)))
            elif sort_by == 'price_desc':
                indicators.sort(key=lambda x: (float(x.price or 0), x.id or 0), reverse=True)
            elif sort_by == 'rating':
                indicators.sort(key=lambda x: ((x.avg_rating or 0), (x.rating_count or 0)), reverse=True)
            else:
                indicators.sort(key=lambda x: x.id or 0, reverse=True)

            total = len(indicators)
            offset = (page - 1) * page_size
            rows = indicators[offset:offset + page_size]

            return {
                'items': [self._indicator_to_market_item(row, user_id=user_id) for row in rows],
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size if total > 0 else 0,
            }
        except Exception as e:
            logger.error(f"get_market_indicators failed: {e}")
            return {'items': [], 'total': 0, 'page': 1, 'page_size': page_size, 'total_pages': 0}

    def get_indicator_detail(self, indicator_id: int, user_id: int = None) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as session:
                indicator = CommunityRepository(session).get_indicator_by_id(indicator_id)
            if not indicator:
                return None
            if not indicator.publish_to_community and indicator.user_id != user_id:
                return None
            detail = self._indicator_to_market_item(indicator, user_id=user_id)
            detail.update({
                'description': indicator.description or '',
                'publish_to_community': bool(indicator.publish_to_community),
                'review_status': indicator.review_status,
                'updated_at': indicator.updated_at.isoformat() if indicator.updated_at else None,
                'code': indicator.code if indicator.user_id == user_id else None,
                'local_copy_id': None,
                'has_update': False,
            })
            return detail
        except Exception as e:
            logger.error(f"get_indicator_detail failed: {e}")
            return None


_community_service_instance: CommunityService | None = None


def get_community_service() -> CommunityService:
    global _community_service_instance
    if _community_service_instance is None:
        _community_service_instance = CommunityService()
    return _community_service_instance
