"""Portfolio API routes (local-only)."""
from flask import Blueprint, request, jsonify, g
import os
import json
import traceback
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from app.database.repositories.portfolio_route_repository import PortfolioRouteRepository
from app.database.session import get_session
from app.services.kline import KlineService
from app.utils.logger import get_logger
from app.utils.auth import login_required
from app.services.symbol_name import resolve_symbol_name
from app.data.market_symbols_seed import get_symbol_name as seed_get_symbol_name

logger = get_logger(__name__)
portfolio_bp = Blueprint('portfolio', __name__)
kline_service = KlineService()


def _portfolio_executor_workers() -> int:
    try:
        v = int(os.getenv("PORTFOLIO_EXECUTOR_WORKERS", "3"))
        return v if v > 0 else 3
    except Exception:
        return 3


executor = ThreadPoolExecutor(max_workers=_portfolio_executor_workers())
REQUEST_INTERVAL = 0.3
_request_lock = threading.Lock()
_last_request_time = {}


def _now_ts() -> int:
    return int(time.time())


def _normalize_symbol(symbol: str) -> str:
    return (symbol or '').strip().upper()


def _safe_json_loads(value, default=None):
    if default is None:
        default = {}
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return default
    return default


def _get_single_price(market: str, symbol: str, force_refresh: bool = False) -> dict:
    try:
        with _request_lock:
            now = time.time()
            last_time = _last_request_time.get(market, 0)
            wait_time = REQUEST_INTERVAL - (now - last_time)
            if wait_time > 0:
                time.sleep(wait_time)
            _last_request_time[market] = time.time()
        price_data = kline_service.get_realtime_price(market, symbol, force_refresh=force_refresh)
        return {'market': market, 'symbol': symbol, 'price': price_data.get('price', 0), 'change': price_data.get('change', 0), 'changePercent': price_data.get('changePercent', 0), 'source': price_data.get('source', 'unknown')}
    except Exception as e:
        logger.error(f"Failed to fetch price {market}:{symbol} - {str(e)}")
        return {'market': market, 'symbol': symbol, 'price': 0, 'change': 0, 'changePercent': 0, 'source': 'error'}


@portfolio_bp.route('/summary', methods=['GET'])
@login_required
def get_portfolio_summary():
    """
    ---
    tags:
      - Portfolio/Summary
    summary: "Get portfolio summary"
    description: "Aggregate all positions for the current user, computing total cost, market value, P&L, and market distribution."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: refresh
        in: query
        type: string
        required: false
        description: "Force price refresh (1/true/yes)"
    responses:
      200:
        description: Successful response with portfolio summary
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
              properties:
                total_cost:
                  type: number
                  description: "Total cost basis"
                total_market_value:
                  type: number
                  description: "Total current market value"
                total_pnl:
                  type: number
                  description: "Total profit and loss"
                total_pnl_percent:
                  type: number
                  description: "Total P&L percentage"
                position_count:
                  type: integer
                  description: "Number of open positions"
                market_distribution:
                  type: array
                  description: "Market value distribution by market"
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        force_refresh = request.args.get('refresh', '').lower() in ('1', 'true', 'yes')
        with get_session() as session:
            rows = PortfolioRouteRepository(session).list_positions(user_id)
        if not rows:
            return jsonify({'code': 1, 'msg': 'success', 'data': {'total_cost': 0, 'total_market_value': 0, 'total_pnl': 0, 'total_pnl_percent': 0, 'position_count': 0, 'market_distribution': []}})
        price_futures = {}
        for row in rows:
            key = f"{row.market}:{row.symbol}"
            if key not in price_futures:
                price_futures[key] = executor.submit(_get_single_price, row.market, row.symbol, force_refresh)
        price_map = {}
        for key, future in price_futures.items():
            try:
                price_map[key] = future.result(timeout=10)
            except Exception:
                pass
        total_cost = 0
        total_market_value = 0
        total_pnl = 0
        market_values = {}
        for row in rows:
            quantity = float(row.quantity or 0)
            entry_price = float(row.entry_price or 0)
            current_price = float((price_map.get(f"{row.market}:{row.symbol}", {}) or {}).get('price') or 0)
            cost = entry_price * quantity
            market_val = current_price * quantity
            pnl = (current_price - entry_price) * quantity if (row.side or 'long') == 'long' else (entry_price - current_price) * quantity
            total_cost += cost
            total_market_value += market_val
            total_pnl += pnl
            market_values[row.market] = market_values.get(row.market, 0) + market_val
        market_distribution = []
        for market, value in market_values.items():
            percent = round(value / total_market_value * 100, 2) if total_market_value > 0 else 0
            market_distribution.append({'market': market, 'value': round(value, 2), 'percent': percent})
        market_distribution.sort(key=lambda x: x['value'], reverse=True)
        return jsonify({'code': 1, 'msg': 'success', 'data': {'total_cost': round(total_cost, 2), 'total_market_value': round(total_market_value, 2), 'total_pnl': round(total_pnl, 2), 'total_pnl_percent': round(total_pnl / total_cost * 100, 2) if total_cost > 0 else 0, 'position_count': len(rows), 'market_distribution': market_distribution}})
    except Exception as e:
        logger.error(f"get_portfolio_summary failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500
