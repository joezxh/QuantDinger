"""Backtest API routes"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import calendar
import traceback
import os

from app.services.backtest import BacktestService
from app.utils.logger import get_logger
from app.utils.auth import login_required
from app.utils.safe_exec import validate_code_safety

logger = get_logger(__name__)
backtest_bp = Blueprint('backtest', __name__)
backtest_service = BacktestService()


def _add_months(dt: datetime, months: int) -> datetime:
    month_index = (dt.month - 1) + int(months or 0)
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def _backtest_range_limit(timeframe: str, start_date: datetime) -> tuple[datetime, str]:
    tf = str(timeframe or '').strip()
    if tf == '1m':
        return _add_months(start_date, 1), '1 month'
    if tf == '5m':
        return _add_months(start_date, 6), '6 months'
    if tf in ['15m', '30m']:
        return _add_months(start_date, 12), '1 year'
    return _add_months(start_date, 36), '3 years'


@backtest_bp.route('/backtest/precision-info', methods=['GET'])
def get_precision_info():
    """
    ---
    tags:
      - Strategies/Backtest
    summary: "Get backtest precision info"
    description: "Calculate and return the execution timeframe precision based on start/end dates and market type."
    produces:
      - application/json
    parameters:
      - name: market
        in: query
        type: string
        required: false
        default: crypto
        description: "Market type (crypto, stocks, etc.)"
      - name: startDate
        in: query
        type: string
        required: true
        description: "Start date in YYYY-MM-DD format"
      - name: endDate
        in: query
        type: string
        required: true
        description: "End date in YYYY-MM-DD format"
    responses:
      200:
        description: Success
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
        description: Missing or invalid parameters
      500:
        description: Internal server error
    """
    try:
        market = request.args.get('market', 'crypto')
        start_date_str = request.args.get('startDate', '')
        end_date_str = request.args.get('endDate', '')
        if not start_date_str or not end_date_str:
            return jsonify({'code': 0, 'msg': 'startDate and endDate are required'}), 400
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        _, precision_info = backtest_service.get_execution_timeframe(start_date, end_date, market)
        return jsonify({'code': 1, 'msg': 'success', 'data': precision_info})
    except Exception as e:
        logger.error(f"Get precision info failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 400


@backtest_bp.route('/backtest', methods=['POST'])
@login_required
def run_backtest():
    """
    ---
    tags:
      - Strategies/Backtest
    summary: "Run backtest simulation"
    description: "Execute a backtest using indicator code and historical K-line data. Returns trade records and performance statistics."
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
            - indicatorCode
            - symbol
            - market
            - timeframe
            - startDate
            - endDate
          properties:
            indicatorCode:
              type: string
              description: "Indicator Python code"
            indicatorId:
              type: integer
              description: "Indicator ID (optional)"
            symbol:
              type: string
              description: "Trading pair or stock symbol"
            market:
              type: string
              description: "Market type (crypto, stocks, etc.)"
            timeframe:
              type: string
              description: "Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1D, etc.)"
            startDate:
              type: string
              description: "Start date in YYYY-MM-DD format"
            endDate:
              type: string
              description: "End date in YYYY-MM-DD format"
            initialCapital:
              type: number
              default: 10000
              description: "Initial capital amount"
            commission:
              type: number
              default: 0.001
              description: "Commission rate (e.g. 0.001 = 0.1%)"
            slippage:
              type: number
              default: 0.0
              description: "Slippage rate"
            leverage:
              type: integer
              default: 1
              description: "Leverage multiplier"
            tradeDirection:
              type: string
              default: long
              description: "Trade direction (long/short/both)"
            strategyConfig:
              type: object
              description: "Additional strategy configuration"
            enableMtf:
              type: boolean
              default: true
              description: "Enable multi-timeframe analysis"
            persist:
              type: boolean
              default: true
              description: "Persist backtest results to database"
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
      400:
        description: Bad request - missing or invalid parameters
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 0, 'msg': 'Request body is required', 'data': None}), 400
        user_id = g.user_id
        indicator_code = data.get('indicatorCode', '')
        is_safe_code, unsafe_reason = validate_code_safety(indicator_code or '')
        if not is_safe_code:
            return jsonify({'code': 0, 'msg': f'Unsafe indicator code: {unsafe_reason}', 'data': None}), 400
        symbol = data.get('symbol', '')
        market = data.get('market', '')
        timeframe = data.get('timeframe', '1D')
        start_date_str = data.get('startDate', '')
        end_date_str = data.get('endDate', '')
        if not all([indicator_code, symbol, market, timeframe, start_date_str, end_date_str]):
            return jsonify({'code': 0, 'msg': 'Missing required parameters', 'data': None}), 400
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        max_end_date, max_range_text = _backtest_range_limit(timeframe, start_date)
        if end_date > max_end_date:
            return jsonify({'code': 0, 'msg': f'Backtest range exceeds limit: timeframe {timeframe} supports up to {max_range_text}', 'data': None}), 400
        result = backtest_service.run(
            user_id=user_id,
            indicator_code=indicator_code,
            indicator_id=data.get('indicatorId'),
            symbol=symbol,
            market=market,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_capital=float(data.get('initialCapital', 10000)),
            commission=float(data.get('commission', 0.001)),
            slippage=float(data.get('slippage', 0.0)),
            leverage=int(data.get('leverage', 1)),
            trade_direction=data.get('tradeDirection', 'long'),
            strategy_config=data.get('strategyConfig') or {},
            enable_mtf=bool(data.get('enableMtf', True)),
            persist=bool(data.get('persist', True)),
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"run_backtest failed: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500
