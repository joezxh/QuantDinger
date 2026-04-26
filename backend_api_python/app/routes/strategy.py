"""Trading Strategy API Routes"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import json
import re
import traceback

from app.services.strategy import StrategyService
from app.services.backtest import BacktestService
from app.services.strategy_snapshot import StrategySnapshotResolver
from app import get_trading_executor
from app.utils.logger import get_logger
from app.utils.auth import login_required
from app.database.session import get_session
from app.database.repositories.notification_repository import NotificationRepository

logger = get_logger(__name__)

strategy_bp = Blueprint('strategy', __name__)


def _normalize_trade_row_for_api(trade: dict) -> dict:
    try:
        from decimal import Decimal
    except Exception:
        Decimal = ()
    out = dict(trade)
    for k in ("price", "amount", "value", "commission", "profit"):
        v = out.get(k)
        if isinstance(v, Decimal):
            out[k] = float(v)
    return out


_strategy_service = None
_backtest_service = None


def get_strategy_service() -> StrategyService:
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategyService()
    return _strategy_service


def get_backtest_service() -> BacktestService:
    global _backtest_service
    if _backtest_service is None:
        _backtest_service = BacktestService()
    return _backtest_service


@strategy_bp.route('/strategies', methods=['GET'])
@login_required
def list_strategies():
    """
    ---
    tags:
      - Strategies/Management
    summary: "List trading strategies"
    description: "Return the current user's list of trading strategy records."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with strategy list
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
                strategies:
                  type: array
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        items = get_strategy_service().list_strategies(user_id=user_id)
        return jsonify({'code': 1, 'msg': 'success', 'data': {'strategies': items}})
    except Exception as e:
        logger.error(f"list_strategies failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': {'strategies': []}}), 500


@strategy_bp.route('/strategies/detail', methods=['GET'])
@login_required
def get_strategy_detail():
    """
    ---
    tags:
      - Strategies/Management
    summary: "Get strategy detail"
    description: "Retrieve detailed information for a specific trading strategy by ID."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: query
        type: integer
        required: true
        description: "Strategy ID"
    responses:
      200:
        description: Successful response with strategy details
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
      400:
        description: Missing strategy id parameter
      401:
        description: Unauthorized
      404:
        description: Strategy not found
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        strategy_id = request.args.get('id', type=int)
        if not strategy_id:
            return jsonify({'code': 0, 'msg': 'Missing strategy id parameter', 'data': None}), 400
        st = get_strategy_service().get_strategy(strategy_id, user_id=user_id)
        if not st:
            return jsonify({'code': 0, 'msg': 'Strategy not found', 'data': None}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': st})
    except Exception as e:
        logger.error(f"get_strategy_detail failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@strategy_bp.route('/strategies/backtest', methods=['POST'])
@login_required
def run_strategy_backtest():
    """
    ---
    tags:
      - Strategies/Backtest
    summary: "Run strategy backtest"
    description: "Execute a backtest for a specific strategy using its configuration snapshot."
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
          properties:
            strategyId:
              type: integer
              description: "Strategy ID"
            startDate:
              type: string
              description: "Start date in YYYY-MM-DD format"
            endDate:
              type: string
              description: "End date in YYYY-MM-DD format"
            overrideConfig:
              type: object
              description: "Optional config overrides"
    responses:
      200:
        description: Backtest completed successfully
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
                runId:
                  type: integer
                result:
                  type: object
      400:
        description: Bad request - missing or invalid parameters
      401:
        description: Unauthorized
      404:
        description: Strategy not found
      500:
        description: Internal server error
    """
    try:
        payload = request.get_json() or {}
        user_id = g.user_id
        strategy_id = int(payload.get('strategyId') or 0)
        if not strategy_id:
            return jsonify({'code': 0, 'msg': 'strategyId is required', 'data': None}), 400
        start_date_str = str(payload.get('startDate') or '').strip()
        end_date_str = str(payload.get('endDate') or '').strip()
        if not start_date_str or not end_date_str:
            return jsonify({'code': 0, 'msg': 'startDate and endDate are required', 'data': None}), 400
        strategy = get_strategy_service().get_strategy(strategy_id, user_id=user_id)
        if not strategy:
            return jsonify({'code': 0, 'msg': 'Strategy not found', 'data': None}), 404
        resolver = StrategySnapshotResolver(user_id=user_id)
        snapshot = resolver.resolve(strategy, payload.get('overrideConfig') or {})
        snapshot['user_id'] = user_id
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        svc = get_backtest_service()
        result = svc.run_strategy_snapshot(snapshot, start_date=start_date, end_date=end_date)
        run_id = svc.persist_run(
            user_id=user_id,
            indicator_id=snapshot.get('indicator_id'),
            strategy_id=snapshot.get('strategy_id'),
            strategy_name=snapshot.get('strategy_name') or '',
            run_type=snapshot.get('run_type') or 'strategy_indicator',
            market=snapshot.get('market') or '',
            symbol=snapshot.get('symbol') or '',
            timeframe=snapshot.get('timeframe') or '',
            start_date_str=start_date_str,
            end_date_str=end_date_str,
            initial_capital=float(snapshot.get('initial_capital') or 0),
            commission=float(snapshot.get('commission') or 0),
            slippage=float(snapshot.get('slippage') or 0),
            leverage=int(snapshot.get('leverage') or 1),
            trade_direction=str(snapshot.get('trade_direction') or 'long'),
            strategy_config=snapshot.get('strategy_config') or {},
            config_snapshot=snapshot.get('config_snapshot') or {},
            status='success',
            error_message='',
            result=result,
            code=snapshot.get('code') or '',
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': {'runId': run_id, 'result': result}})
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"run_strategy_backtest failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@strategy_bp.route('/strategies/backtest/history', methods=['GET'])
@login_required
def get_strategy_backtest_history():
    """
    ---
    tags:
      - Strategies/Backtest
    summary: "Get strategy backtest history"
    description: "Retrieve backtest execution history for a specific strategy."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: strategyId
        in: query
        type: integer
        required: true
        description: "Strategy ID"
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: "Max records to return, up to 200"
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: "Offset for pagination"
    responses:
      200:
        description: Successful response with backtest history
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
      400:
        description: Missing strategyId
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        strategy_id = int(request.args.get('strategyId') or request.args.get('id') or 0)
        if not strategy_id:
            return jsonify({'code': 0, 'msg': 'strategyId is required', 'data': None}), 400
        limit = max(1, min(int(request.args.get('limit') or 50), 200))
        offset = max(0, int(request.args.get('offset') or 0))
        rows = get_backtest_service().list_runs(user_id=user_id, strategy_id=strategy_id, limit=limit, offset=offset)
        rows = [r for r in rows if str(r.get('run_type') or '').startswith('strategy_')]
        return jsonify({'code': 1, 'msg': 'success', 'data': rows})
    except Exception as e:
        logger.error(f"get_strategy_backtest_history failed: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


# ==================== Strategy Notifications ====================


@strategy_bp.route('/strategies/notifications', methods=['GET'])
@login_required
def list_notifications():
    """
    ---
    tags:
      - Strategies/Notifications
    summary: "List strategy notifications"
    description: "Return the current user's strategy notifications with optional read status filter."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: "Max records to return, up to 200"
      - name: offset
        in: query
        type: integer
        required: false
        default: 0
        description: "Offset for pagination"
      - name: is_read
        in: query
        type: integer
        required: false
        description: "Filter by read status (0=unread, 1=read)"
    responses:
      200:
        description: Successful response with notification list
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
                items:
                  type: array
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        is_read_param = request.args.get('is_read')
        is_read = int(is_read_param) if is_read_param is not None else None

        with get_session() as session:
            repo = NotificationRepository(session)
            items = repo.list_notifications_by_user(
                user_id=user_id, is_read=is_read,
                limit=min(limit, 200), offset=max(offset, 0),
            )
            result = []
            for n in items:
                result.append({
                    'id': n.id,
                    'strategy_id': n.strategy_id,
                    'symbol': n.symbol,
                    'signal_type': n.signal_type,
                    'channels': n.channels,
                    'title': n.title,
                    'message': n.message,
                    'payload_json': n.payload_json,
                    'is_read': n.is_read,
                    'created_at': str(n.created_at) if n.created_at else None,
                })
            return jsonify({'code': 1, 'msg': 'success', 'data': {'items': result}})
    except Exception as e:
        logger.error(f"list_notifications failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@strategy_bp.route('/strategies/notifications/unread-count', methods=['GET'])
@login_required
def unread_notification_count():
    """
    ---
    tags:
      - Strategies/Notifications
    summary: "Get unread notification count"
    description: "Return the number of unread notifications for the current user (header badge)."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with unread count
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
                unread:
                  type: integer
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        with get_session() as session:
            repo = NotificationRepository(session)
            items = repo.list_notifications_by_user(
                user_id=user_id, is_read=0, limit=99999,
            )
            count = len(items)
            return jsonify({'code': 1, 'msg': 'success', 'data': {'unread': count}})
    except Exception as e:
        logger.error(f"unread_notification_count failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': {'unread': 0}}), 500


@strategy_bp.route('/strategies/notifications/read', methods=['POST'])
@login_required
def mark_notification_read():
    """
    ---
    tags:
      - Strategies/Notifications
    summary: "Mark notification as read"
    description: "Mark a single strategy notification as read by its ID."
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
            - id
          properties:
            id:
              type: integer
              description: "Notification ID"
    responses:
      200:
        description: Notification marked as read
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: Marked as read
      400:
        description: Missing notification id
      401:
        description: Unauthorized
      403:
        description: Permission denied
      404:
        description: Notification not found
      500:
        description: Internal server error
    """
    try:
        data = request.get_json() or {}
        notification_id = data.get('id')
        if not notification_id:
            return jsonify({'code': 0, 'msg': 'Notification id required'}), 400

        user_id = g.user_id
        with get_session() as session:
            repo = NotificationRepository(session)
            notification = repo.get_notification_by_id(notification_id)
            if not notification:
                return jsonify({'code': 0, 'msg': 'Notification not found'}), 404
            if notification.user_id != user_id:
                return jsonify({'code': 0, 'msg': 'Permission denied'}), 403
            repo.mark_read(notification_id)
            return jsonify({'code': 1, 'msg': 'Marked as read'})
    except Exception as e:
        logger.error(f"mark_notification_read failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@strategy_bp.route('/strategies/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """
    ---
    tags:
      - Strategies/Notifications
    summary: "Mark all notifications as read"
    description: "Mark all unread notifications as read for the current user."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: All notifications marked as read
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        with get_session() as session:
            repo = NotificationRepository(session)
            count = repo.mark_all_read(user_id)
            return jsonify({'code': 1, 'msg': f'{count} notifications marked as read'})
    except Exception as e:
        logger.error(f"mark_all_notifications_read failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500


@strategy_bp.route('/strategies/notifications/clear', methods=['DELETE'])
@login_required
def clear_notifications():
    """
    ---
    tags:
      - Strategies/Notifications
    summary: "Clear all notifications"
    description: "Delete all notifications for the current user."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Notifications cleared successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        with get_session() as session:
            repo = NotificationRepository(session)
            count = repo.clear_all(user_id)
            return jsonify({'code': 1, 'msg': f'{count} notifications cleared'})
    except Exception as e:
        logger.error(f"clear_notifications failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500
