"""Market API routes (local-only)."""
from flask import Blueprint, request, jsonify, g
import os
import traceback
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.kline import KlineService
from app.utils.logger import get_logger
from app.database.repositories.market_route_repository import MarketRouteRepository
from app.database.session import get_session
from app.utils.config_loader import load_addon_config
from app.utils.auth import login_required
from app.data.market_symbols_seed import get_hot_symbols as seed_get_hot_symbols, search_symbols as seed_search_symbols, get_symbol_name as seed_get_symbol_name
from app.services.symbol_name import resolve_symbol_name

logger = get_logger(__name__)
market_bp = Blueprint('market', __name__)
kline_service = KlineService()


def _market_executor_workers() -> int:
    try:
        v = int(os.getenv("MARKET_EXECUTOR_WORKERS", "6"))
        return v if v > 0 else 6
    except Exception:
        return 6


executor = ThreadPoolExecutor(max_workers=_market_executor_workers())


def _normalize_symbol(symbol: str) -> str:
    return (symbol or '').strip().upper()


@market_bp.route('/watchlist/get', methods=['GET'])
@login_required
def get_watchlist():
    """
    ---
    tags:
      - Market/Watchlist
    summary: "Get user watchlist"
    description: "Return the current user's watchlist with auto-resolved asset names."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with watchlist items
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
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  market:
                    type: string
                  symbol:
                    type: string
                  name:
                    type: string
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        with get_session() as session:
            rows = MarketRouteRepository(session).list_watchlist(user_id)
            out = []
            changed = False
            for row in rows:
                current_name = (row.name or '').strip()
                if not current_name or current_name == row.symbol:
                    resolved = resolve_symbol_name(row.market, row.symbol) or seed_get_symbol_name(row.market, row.symbol)
                    if resolved and resolved != current_name:
                        row.name = resolved
                        changed = True
                out.append({'id': row.id, 'market': row.market, 'symbol': row.symbol, 'name': row.name})
        return jsonify({'code': 1, 'msg': 'success', 'data': out})
    except Exception as e:
        logger.error(f"get_watchlist failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': []}), 500


@market_bp.route('/watchlist/add', methods=['POST'])
@login_required
def add_watchlist():
    """
    ---
    tags:
      - Market/Watchlist
    summary: "Add symbol to watchlist"
    description: "Add a trading symbol to the current user's watchlist."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - market
            - symbol
          properties:
            market:
              type: string
              description: "Market type (USStock, Crypto, etc.)"
            symbol:
              type: string
              description: "Trading symbol"
            name:
              type: string
              description: "Display name (optional, auto-resolved if empty)"
    responses:
      200:
        description: Symbol added to watchlist
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
      400:
        description: Missing market or symbol
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        market = (data.get('market') or '').strip()
        symbol = _normalize_symbol(data.get('symbol'))
        name_in = (data.get('name') or '').strip()
        if not market or not symbol:
            return jsonify({'code': 0, 'msg': 'Missing market or symbol', 'data': None}), 400
        resolved = resolve_symbol_name(market, symbol) or seed_get_symbol_name(market, symbol)
        name = name_in or resolved or symbol
        with get_session() as session:
            MarketRouteRepository(session).upsert_watchlist_item(user_id=user_id, market=market, symbol=symbol, name=name)
        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"add_watchlist failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@market_bp.route('/watchlist/remove', methods=['POST'])
@login_required
def remove_watchlist():
    """
    ---
    tags:
      - Market/Watchlist
    summary: "Remove symbol from watchlist"
    description: "Remove a trading symbol from the current user's watchlist."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - symbol
          properties:
            symbol:
              type: string
              description: "Trading symbol to remove"
    responses:
      200:
        description: Symbol removed from watchlist
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
      400:
        description: Missing symbol
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        symbol = _normalize_symbol(data.get('symbol'))
        if not symbol:
            return jsonify({'code': 0, 'msg': 'Missing symbol', 'data': None}), 400
        with get_session() as session:
            MarketRouteRepository(session).delete_watchlist_by_symbol(user_id, symbol)
        return jsonify({'code': 1, 'msg': 'success', 'data': None})
    except Exception as e:
        logger.error(f"remove_watchlist failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500
