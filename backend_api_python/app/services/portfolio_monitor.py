"""Portfolio Monitor Service.
Runs scheduled AI analysis on manual positions and sends notifications.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.database.repositories.portfolio_repository import PortfolioRepository
from app.database.session import get_session
from app.services.kline import KlineService
from app.utils.logger import get_logger

logger = get_logger(__name__)
DEFAULT_USER_ID = 1


def _safe_json_loads(value, default=None):
    if default is None:
        default = {}
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return default
    return default


def _get_positions_for_monitor(position_ids: List[int] = None, user_id: int = None) -> List[Dict[str, Any]]:
    try:
        kline_service = KlineService()
        effective_user_id = user_id if user_id is not None else DEFAULT_USER_ID
        with get_session() as session:
            rows = PortfolioRepository(session).list_manual_positions(effective_user_id, position_ids=position_ids)
        positions = []
        for row in rows:
            entry_price = float(row.entry_price or 0)
            quantity = float(row.quantity or 0)
            side = row.side or 'long'
            current_price = 0
            try:
                price_data = kline_service.get_realtime_price(row.market, row.symbol)
                current_price = float(price_data.get('price') or 0)
            except Exception:
                pass
            pnl = (current_price - entry_price) * quantity if side == 'long' else (entry_price - current_price) * quantity
            pnl_percent = round(pnl / (entry_price * quantity) * 100, 2) if entry_price * quantity > 0 else 0
            positions.append({
                'id': row.id,
                'market': row.market,
                'symbol': row.symbol,
                'name': row.name or row.symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': entry_price,
                'current_price': current_price,
                'pnl': round(pnl, 2),
                'pnl_percent': pnl_percent,
                'group_name': row.group_name,
            })
        return positions
    except Exception as e:
        logger.error(f"_get_positions_for_monitor failed: {e}")
        return []
