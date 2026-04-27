"""
Experiment orchestration API routes.
"""

import json
import queue
import threading

from flask import Blueprint, Response, g, jsonify, request

from app.services.experiment.runner import ExperimentRunnerService
from app.utils.auth import login_required
from app.utils.logger import get_logger

logger = get_logger(__name__)

experiment_bp = Blueprint('experiment', __name__)
experiment_runner = ExperimentRunnerService()


@experiment_bp.route('/regime/detect', methods=['POST'])
@login_required
def detect_market_regime():
    """
    ---
    tags:
      - Experiment/Regime Detection
    summary: "Detect current market regime"
    description: "Analyze and detect the current market regime for a given symbol, timeframe, and date range."
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
              description: "Trading symbol (e.g., BTC/USDT)"
            timeframe:
              type: string
              default: 1d
              description: "K-line timeframe (1m, 5m, 15m, 1h, 4h, 1d, etc.)"
            start_date:
              type: string
              description: "Start date for analysis (YYYY-MM-DD)"
            end_date:
              type: string
              description: "End date for analysis (YYYY-MM-DD)"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        payload = request.get_json() or {}
        regime = experiment_runner.detect_regime(payload)
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': regime,
        })
    except Exception as exc:
        logger.error("detect_market_regime failed", exc_info=True)
        return jsonify({
            'code': 0,
            'msg': str(exc),
            'data': None,
        }), 400


@experiment_bp.route('/pipeline/run', methods=['POST'])
@login_required
def run_experiment_pipeline():
    """
    ---
    tags:
      - Experiment/Pipeline
    summary: "Run experiment pipeline (legacy)"
    description: "Legacy grid-search pipeline kept for backward compatibility."
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
              description: "Trading symbol (e.g., BTC/USDT)"
            strategy_type:
              type: string
              description: "Strategy type identifier"
            parameters:
              type: object
              description: "Grid-search parameters with ranges"
            date_range:
              type: object
              description: "Backtest date range"
              properties:
                start:
                  type: string
                  description: "Start date (YYYY-MM-DD)"
                end:
                  type: string
                  description: "End date (YYYY-MM-DD)"
            market_type:
              type: string
              default: crypto
              description: "Market type (crypto, stock, forex)"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        payload = request.get_json() or {}
        if not payload:
            return jsonify({'code': 0, 'msg': 'Request body is required', 'data': None}), 400

        data = experiment_runner.run_pipeline(
            user_id=int(g.user_id or 1),
            payload=payload,
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': data})
    except Exception as exc:
        logger.error("run_experiment_pipeline failed", exc_info=True)
        return jsonify({'code': 0, 'msg': str(exc), 'data': None}), 400


@experiment_bp.route('/ai-optimize', methods=['POST'])
@login_required
def ai_optimize():
    """
    ---
    tags:
      - Experiment/AI Optimization
    summary: "AI-powered optimization with SSE streaming"
    description: "LLM-driven multi-round optimization pipeline with progress streaming via Server-Sent Events."
    produces:
      - text/event-stream
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
              description: "Trading symbol (e.g., BTC/USDT)"
            strategy_description:
              type: string
              description: "Natural language description of the strategy to optimize"
            objective:
              type: string
              default: sharpe_ratio
              description: "Optimization objective (sharpe_ratio, sortino_ratio, total_return, max_drawdown)"
            constraints:
              type: object
              description: "Optimization constraints"
            timeframe:
              type: string
              default: 1d
              description: "K-line timeframe"
    responses:
      200:
        description: SSE stream with progress events and final result
        schema:
          type: string
          format: binary
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    payload = request.get_json() or {}
    if not payload:
        return jsonify({'code': 0, 'msg': 'Request body is required', 'data': None}), 400

    user_id = int(g.user_id or 1)
    progress_queue: queue.Queue = queue.Queue()

    def on_progress(data):
        progress_queue.put(data)

    def run():
        try:
            result = experiment_runner.run_ai_pipeline(
                user_id=user_id,
                payload=payload,
                on_progress=on_progress,
            )
            progress_queue.put({'event': '__final__', 'data': result})
        except Exception as exc:
            logger.error("ai_optimize pipeline failed", exc_info=True)
            progress_queue.put({'event': '__error__', 'msg': str(exc)})

    worker = threading.Thread(target=run, daemon=True)
    worker.start()

    def generate():
        while True:
            try:
                item = progress_queue.get(timeout=600)
            except queue.Empty:
                yield _sse('error', {'msg': 'Pipeline timeout'})
                break

            if item.get('event') == '__final__':
                yield _sse('done', item['data'])
                break
            elif item.get('event') == '__error__':
                yield _sse('error', {'msg': item.get('msg', 'Unknown error')})
                break
            else:
                yield _sse('progress', item)

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@experiment_bp.route('/ai-optimize-sync', methods=['POST'])
@login_required
def ai_optimize_sync():
    """
    ---
    tags:
      - Experiment/AI Optimization
    summary: "AI optimization (sync, non-streaming)"
    description: "Non-streaming version of AI optimization for simpler client integration."
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
              description: "Trading symbol (e.g., BTC/USDT)"
            strategy_description:
              type: string
              description: "Natural language description of the strategy to optimize"
            objective:
              type: string
              default: sharpe_ratio
              description: "Optimization objective"
            constraints:
              type: object
              description: "Optimization constraints"
            timeframe:
              type: string
              default: 1d
              description: "K-line timeframe"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    payload = request.get_json() or {}
    if not payload:
        return jsonify({'code': 0, 'msg': 'Request body is required', 'data': None}), 400

    try:
        data = experiment_runner.run_ai_pipeline(
            user_id=int(g.user_id or 1),
            payload=payload,
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': data})
    except Exception as exc:
        logger.error("ai_optimize_sync failed", exc_info=True)
        return jsonify({'code': 0, 'msg': str(exc), 'data': None}), 400


@experiment_bp.route('/structured-tune', methods=['POST'])
@login_required
def structured_tune():
    """
    ---
    tags:
      - Experiment/Structured Tuning
    summary: "Run structured parameter tuning"
    description: "Grid or random search over an explicit parameter space without LLM involvement."
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
              description: "Trading symbol (e.g., BTC/USDT)"
            parameter_space:
              type: object
              description: "Dictionary of parameter names to value ranges"
            search_method:
              type: string
              default: grid
              description: "Search method - grid or random"
            max_iterations:
              type: integer
              default: 100
              description: "Max iterations for random search"
            metric:
              type: string
              default: sharpe_ratio
              description: "Metric to optimize"
            timeframe:
              type: string
              default: 1d
              description: "K-line timeframe"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    payload = request.get_json() or {}
    if not payload:
        return jsonify({'code': 0, 'msg': 'Request body is required', 'data': None}), 400

    try:
        data = experiment_runner.run_structured_tune(
            user_id=int(g.user_id or 1),
            payload=payload,
        )
        return jsonify({'code': 1, 'msg': 'success', 'data': data})
    except ValueError as exc:
        return jsonify({'code': 0, 'msg': str(exc), 'data': None}), 400
    except Exception as exc:
        logger.error("structured_tune failed", exc_info=True)
        return jsonify({'code': 0, 'msg': str(exc), 'data': None}), 400


@experiment_bp.route('/save-strategy', methods=['POST'])
@login_required
def save_experiment_strategy():
    """
    ---
    tags:
      - Experiment/Strategy
    summary: "Save experiment as strategy"
    description: "Save the best experiment candidate as a permanent strategy record."
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
            - bestOutput
            - strategyName
          properties:
            bestOutput:
              type: object
              description: "Best experiment candidate output to save as strategy"
            strategyName:
              type: string
              description: "Name for the saved strategy"
            marketCategory:
              type: string
              default: Crypto
              description: "Market category (Crypto, Stock, Forex)"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        payload = request.get_json() or {}
        best_output = payload.get('bestOutput') or payload.get('bestStrategyOutput')
        if not best_output:
            return jsonify({'code': 0, 'msg': 'bestOutput is required', 'data': None}), 400

        strategy_name = (payload.get('strategyName') or '').strip()
        if not strategy_name:
            return jsonify({'code': 0, 'msg': 'strategyName is required', 'data': None}), 400

        market_category = payload.get('marketCategory') or 'Crypto'
        strategy_id = experiment_runner.save_as_strategy(
            user_id=int(g.user_id or 1),
            best_output=best_output,
            strategy_name=strategy_name,
            market_category=market_category,
        )
        return jsonify({
            'code': 1,
            'msg': 'Strategy saved',
            'data': {'strategyId': strategy_id},
        })
    except Exception as exc:
        logger.error("save_experiment_strategy failed", exc_info=True)
        return jsonify({'code': 0, 'msg': str(exc), 'data': None}), 400


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str, ensure_ascii=False)}\n\n"
