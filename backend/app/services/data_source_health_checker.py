# -*- coding: utf-8 -*-
"""
数据源健康检查定时任务

后台线程定时巡检所有已注册数据源，检查连通性和响应时间。
检查结果写入 data_source_health 表，并联动 CircuitBreaker 熔断器。

集成点: Flask app 启动钩子中调用 start_health_checker()
"""
import time
import threading
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)

# 默认检查间隔（秒）
DEFAULT_CHECK_INTERVAL = 300  # 5 分钟

# 每个 Provider 的健康检查测试参数
_HEALTH_CHECK_PARAMS = {
    "crypto_ccxt": {"method": "get_ticker", "kwargs": {"symbol": "BTC/USDT"}},
    "us_stock_yfinance": {"method": "get_ticker", "kwargs": {"symbol": "AAPL"}},
    "cn_stock_akshare": {"method": "get_ticker", "kwargs": {"symbol": "000001"}},
    "hk_stock_akshare": {"method": "get_ticker", "kwargs": {"symbol": "00700"}},
    "forex_yfinance": {"method": "get_ticker", "kwargs": {"symbol": "EUR/USD"}},
    "futures_akshare": {"method": "get_ticker", "kwargs": {"symbol": "CL"}},
    "polymarket": {"method": "get_ticker", "kwargs": {"symbol": "BTC"}},
    "macro_fred": {"method": "get_ticker", "kwargs": {"symbol": "DFF"}},
    "macro_bls": {"method": "get_ticker", "kwargs": {"symbol": "LNS14000000"}},
    "macro_worldbank": {"method": "get_ticker", "kwargs": {"symbol": "NY.GDP.MKTP.CD:US"}},
    "cn_stock_tushare": {"method": "get_ticker", "kwargs": {"symbol": "000001.SZ"}},
    "cn_stock_baostock": {"method": "get_ticker", "kwargs": {"symbol": "sh.600000"}},
    "crypto_coingecko": {"method": "get_ticker", "kwargs": {"symbol": "BTC/USDT"}},
    "crypto_defillama": {"method": "get_protocols", "kwargs": {}},
    "us_stock_financial_datasets": {"method": "get_ticker", "kwargs": {"symbol": "AAPL"}},
    "futures_cftc": {"method": "get_latest_cot", "kwargs": {"commodity_key": "BTC"}},
    "news_google": {"method": "search", "kwargs": {"query": "stock market", "limit": 1}},
    "news_eastmoney": {"method": "get_financial_news", "kwargs": {"limit": 1}},
    "futures_cboe": {"method": "get_ticker", "kwargs": {"symbol": "VIX"}},
    "macro_bea": {"method": "get_ticker", "kwargs": {"symbol": "nominal_gdp"}},
    "fundamentals_simfin": {"method": "get_ticker", "kwargs": {"symbol": "AAPL"}},
}


class DataSourceHealthChecker:
    """数据源健康检查器"""

    def __init__(self, check_interval: int = DEFAULT_CHECK_INTERVAL):
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_check_results: Dict[str, Dict[str, Any]] = {}

    def start(self):
        """启动后台健康检查线程"""
        if self._running:
            logger.warning("[HealthChecker] Already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="DataSourceHealthChecker",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"[HealthChecker] Started (interval={self.check_interval}s)")

    def stop(self):
        """停止后台健康检查线程"""
        self._stop_event.set()
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("[HealthChecker] Stopped")

    def check_now(self) -> Dict[str, Dict[str, Any]]:
        """立即执行一次全量健康检查"""
        results = {}
        try:
            from app.data_sources.priority_router import get_router
            router = get_router()

            for category, entries in router._entries.items():
                for entry in entries:
                    source_code = entry.source_code
                    result = self._check_single(source_code, entry.provider, category)
                    results[source_code] = result
                    self._last_check_results[source_code] = result

                    # 写入数据库
                    self._write_health_to_db(source_code, category, result)

                    # 联动熔断器
                    self._update_circuit_breaker(source_code, result)

        except Exception as e:
            logger.error(f"[HealthChecker] Check failed: {e}")

        return results

    def get_last_results(self) -> Dict[str, Dict[str, Any]]:
        """获取最近一次检查结果"""
        return dict(self._last_check_results)

    def _check_single(
        self, source_code: str, provider: Any, category: str
    ) -> Dict[str, Any]:
        """检查单个数据源健康状态"""
        params = _HEALTH_CHECK_PARAMS.get(source_code, {"method": "get_ticker", "kwargs": {"symbol": "TEST"}})
        method_name = params["method"]
        kwargs = params["kwargs"]

        start = time.monotonic()
        try:
            method = getattr(provider, method_name, None)
            if method is None:
                return {
                    "status": "no_method",
                    "latency_ms": 0,
                    "error": f"Method {method_name} not found",
                }

            result = method(**kwargs)
            latency_ms = int((time.monotonic() - start) * 1000)

            # 判断是否成功
            if result is None or result == [] or result == {}:
                status = "empty_response"
            elif isinstance(result, dict) and result.get("last") == 0:
                status = "degraded"
            else:
                status = "healthy"

            return {
                "status": status,
                "latency_ms": latency_ms,
                "error": None,
            }
        except Exception as e:
            latency_ms = int((time.monotonic() - start) * 1000)
            return {
                "status": "unhealthy",
                "latency_ms": latency_ms,
                "error": str(e)[:200],
            }

    def _write_health_to_db(
        self, source_code: str, category: str, result: Dict[str, Any]
    ):
        """将检查结果写入 data_source_health 表"""
        try:
            from app.utils.db_postgres import execute_sql
            execute_sql(
                """INSERT INTO data_source_health (source_code, category, status, latency_ms, last_error, last_check_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                   ON CONFLICT (source_code, category) DO UPDATE SET
                     status = EXCLUDED.status,
                     latency_ms = EXCLUDED.latency_ms,
                     last_error = EXCLUDED.last_error,
                     last_check_at = EXCLUDED.last_check_at,
                     updated_at = NOW()""",
                (
                    source_code,
                    category,
                    result["status"],
                    result["latency_ms"],
                    result.get("error") or "",
                ),
                fetch=None,
            )
        except Exception as e:
            logger.debug(f"[HealthChecker] DB write failed for {source_code}: {e}")

    def _update_circuit_breaker(self, source_code: str, result: Dict[str, Any]):
        """联动熔断器"""
        try:
            from app.data_sources.priority_router import get_router
            router = get_router()

            if result["status"] == "healthy":
                router.circuit_breaker.record_success(source_code)
            elif result["status"] in ("unhealthy", "empty_response"):
                router.circuit_breaker.record_failure(
                    source_code, result.get("error") or "health check failed"
                )
        except Exception as e:
            logger.debug(f"[HealthChecker] CB update failed for {source_code}: {e}")

    def _run_loop(self):
        """后台循环检查"""
        # 初始延迟：等应用启动完成
        self._stop_event.wait(30)

        while not self._stop_event.is_set():
            try:
                self.check_now()
            except Exception as e:
                logger.error(f"[HealthChecker] Loop error: {e}")

            self._stop_event.wait(self.check_interval)


# ============================================
# 全局实例
# ============================================

_health_checker: Optional[DataSourceHealthChecker] = None
_checker_lock = threading.Lock()


def get_health_checker() -> DataSourceHealthChecker:
    """获取全局健康检查器实例"""
    global _health_checker
    if _health_checker is None:
        with _checker_lock:
            if _health_checker is None:
                _health_checker = DataSourceHealthChecker()
    return _health_checker


def start_health_checker(check_interval: int = DEFAULT_CHECK_INTERVAL):
    """启动健康检查器（在 Flask app 启动时调用）"""
    global _health_checker
    with _checker_lock:
        if _health_checker is None:
            _health_checker = DataSourceHealthChecker(check_interval=check_interval)
        _health_checker.start()


def stop_health_checker():
    """停止健康检查器"""
    global _health_checker
    if _health_checker is not None:
        _health_checker.stop()
