"""QuantDinger Python API - Flask application factory."""
import math
import logging
import traceback
import atexit

from flask import Flask
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

try:
    from flasgger import Swagger
except Exception:  # pragma: no cover - optional dependency for non-API scripts
    Swagger = None

from app.utils.logger import setup_logger, get_logger


class SafeJSONProvider(DefaultJSONProvider):
    """JSON provider that converts NaN / Infinity to null.

    Python's ``json.dumps`` with ``allow_nan=True`` (the default) emits
    literal ``NaN`` / ``Infinity`` tokens which are **not** valid JSON per
    RFC 8259.  JavaScript's ``JSON.parse()`` will throw on them, breaking
    every frontend consumer.  This provider silently replaces those values
    with ``None`` (→ ``null``) so the output is always spec-compliant.
    """

    @staticmethod
    def default(o):
        return DefaultJSONProvider.default(o)

    def dumps(self, obj, **kwargs):
        kwargs.setdefault("default", self.default)
        return _safe_json_dumps(obj, **kwargs)


def _safe_json_dumps(obj, **kwargs):
    import json
    return json.dumps(_sanitize(obj), **kwargs)


def _sanitize(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


logger = get_logger(__name__)

_trading_executor = None
_pending_order_worker = None


def get_trading_executor():
    global _trading_executor
    if _trading_executor is None:
        from app.services.trading_executor import TradingExecutor
        _trading_executor = TradingExecutor()
    return _trading_executor


def get_pending_order_worker():
    global _pending_order_worker
    if _pending_order_worker is None:
        from app.services.pending_order_worker import PendingOrderWorker
        _pending_order_worker = PendingOrderWorker()
    return _pending_order_worker


def start_polymarket_worker():
    try:
        from app.services.polymarket_worker import get_polymarket_worker
        get_polymarket_worker().start()
    except Exception as e:
        logger.error(f"Failed to start Polymarket worker: {e}")


def start_portfolio_monitor():
    import os
    enabled = os.getenv("ENABLE_PORTFOLIO_MONITOR", "true").lower() == "true"
    if not enabled:
        logger.info("Portfolio monitor is disabled. Set ENABLE_PORTFOLIO_MONITOR=true to enable.")
        return

    debug = os.getenv("PYTHON_API_DEBUG", "false").lower() == "true"
    if debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    try:
        from app.services.portfolio_monitor import start_monitor_service
        start_monitor_service()
    except Exception as e:
        logger.error(f"Failed to start portfolio monitor: {e}")


def start_pending_order_worker():
    import os
    if os.getenv('ENABLE_PENDING_ORDER_WORKER', 'true').lower() != 'true':
        logger.info("Pending order worker is disabled")
        return


def create_app():
    app = Flask(__name__)
    
    # Sync Flask logger with root logger configured in setup_logger()
    # This ensures app.logger calls (and unhandled exceptions) use our console/file handlers.
    app.logger.handlers = logging.getLogger().handlers
    app.logger.setLevel(logging.getLogger().level)

    app.json = SafeJSONProvider(app)
    CORS(app)
    if Swagger is not None:
        Swagger(app)

    # 全局错误处理：捕获未处理的异常并输出详细 traceback
    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e  # Let Flask handle 404, 405 etc normally
        logger.exception(f"Unhandled exception: {e}")
        return {"code": 0, "msg": "internal_server_error", "data": None}, 500

    @app.errorhandler(500)
    def handle_500(e):
        logger.exception(f"Internal Server Error: {e}")
        return {"code": 0, "msg": "internal_server_error", "data": None}, 500

    @app.after_request
    def log_500_errors(response):
        """Log 500 errors to console since Werkzeug INFO logs are suppressed."""
        if response.status_code >= 500:
            from flask import request
            error_msg = f"HTTP {response.status_code} Error on {request.method} {request.path}"
            logger.error(error_msg)
            print(f"[ERROR] {error_msg}")  # Guaranteed console output
        return response

    from app.routes import register_routes
    register_routes(app)

    return app
