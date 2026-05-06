# -*- coding: utf-8 -*-
"""
数据源优先级动态调整器

根据健康检查结果和历史表现数据，动态调整各数据源的优先级：
- 健康数据源：保持或提升优先级
- 频繁故障数据源：降低优先级
- 恢复中的数据源：逐步恢复优先级

调整策略：
1. 基线优先级（baseline_priority）：注册时的静态优先级
2. 健康因子（health_factor）：基于最近 N 次检查结果计算 [0.0, 1.0]
3. 延迟因子（latency_factor）：基于平均响应时间计算 [0.5, 1.0]
4. 最终优先级 = baseline_priority * health_factor * latency_factor
"""
import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from app.utils.logger import get_logger

logger = get_logger(__name__)

# 调整间隔（秒）
DEFAULT_ADJUST_INTERVAL = 600  # 10 分钟

# 延迟阈值（ms）
LATENCY_TIERS = {
    "fast": 500,       # < 500ms: latency_factor = 1.0
    "normal": 2000,    # < 2000ms: latency_factor = 0.9
    "slow": 5000,      # < 5000ms: latency_factor = 0.7
    "very_slow": 10000, # < 10000ms: latency_factor = 0.5
    # >= 10000ms: latency_factor = 0.3
}


def _calc_health_factor(
    healthy_count: int,
    degraded_count: int,
    unhealthy_count: int,
    window: int = 10,
) -> float:
    """
    计算健康因子

    基于最近 N 次检查中各状态的比例，计算一个 [0.0, 1.0] 的健康因子。
    healthy = +1, degraded = +0.5, unhealthy = +0
    """
    total = healthy_count + degraded_count + unhealthy_count
    if total == 0:
        return 0.5  # 无数据时给中间值

    score = (healthy_count * 1.0 + degraded_count * 0.5 + unhealthy_count * 0.0) / min(total, window)
    return max(0.0, min(1.0, score))


def _calc_latency_factor(avg_latency_ms: int) -> float:
    """计算延迟因子"""
    if avg_latency_ms <= 0:
        return 1.0
    if avg_latency_ms < LATENCY_TIERS["fast"]:
        return 1.0
    if avg_latency_ms < LATENCY_TIERS["normal"]:
        return 0.9
    if avg_latency_ms < LATENCY_TIERS["slow"]:
        return 0.7
    if avg_latency_ms < LATENCY_TIERS["very_slow"]:
        return 0.5
    return 0.3


class PriorityAdjuster:
    """数据源优先级动态调整器"""

    def __init__(self, adjust_interval: int = DEFAULT_ADJUST_INTERVAL):
        self.adjust_interval = adjust_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        # 记录每个 source_code 的历史健康状态
        self._health_history: Dict[str, List[Dict[str, Any]]] = {}
        # 记录上一次调整的优先级
        self._last_adjusted: Dict[str, float] = {}

    def start(self):
        """启动后台调整线程"""
        if self._running:
            logger.warning("[PriorityAdjuster] Already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="PriorityAdjuster",
            daemon=True,
        )
        self._thread.start()
        logger.info(f"[PriorityAdjuster] Started (interval={self.adjust_interval}s)")

    def stop(self):
        """停止后台调整线程"""
        self._stop_event.set()
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("[PriorityAdjuster] Stopped")

    def adjust_now(self) -> Dict[str, Dict[str, Any]]:
        """
        立即执行一次优先级调整

        Returns:
            {source_code: {baseline, health_factor, latency_factor, adjusted_priority}}
        """
        results = {}
        try:
            from app.data_sources.priority_router import get_router
            router = get_router()

            # 从健康检查器获取最近结果
            health_results = self._get_health_results()

            for category, entries in router._entries.items():
                for entry in entries:
                    source_code = entry.source_code
                    baseline = entry.priority  # 原始优先级

                    # 计算健康因子
                    health_data = health_results.get(source_code)
                    if health_data:
                        self._record_health(source_code, health_data)

                    stats = self._get_health_stats(source_code)
                    health_factor = _calc_health_factor(
                        stats["healthy"], stats["degraded"], stats["unhealthy"]
                    )

                    # 计算延迟因子
                    avg_latency = stats.get("avg_latency_ms", 0)
                    latency_factor = _calc_latency_factor(avg_latency)

                    # 计算调整后优先级
                    adjusted = round(baseline * health_factor * latency_factor, 2)
                    adjusted = max(adjusted, 1.0)  # 最低保留 1.0

                    # 更新路由器中的优先级
                    old_priority = self._last_adjusted.get(source_code, baseline)
                    if abs(adjusted - old_priority) > 0.5:  # 只有变化超过阈值才更新
                        with router._lock:
                            entry.priority = adjusted
                            router._entries[category].sort(
                                key=lambda e: e.priority, reverse=True
                            )
                        self._last_adjusted[source_code] = adjusted
                        logger.info(
                            f"[PriorityAdjuster] {source_code}: "
                            f"{baseline} -> {adjusted} "
                            f"(health={health_factor:.2f}, latency={latency_factor:.2f})"
                        )
                        # 写入优先级调整日志
                        self._write_priority_log(
                            source_code, category, baseline, adjusted,
                            health_factor, latency_factor, stats
                        )

                    results[source_code] = {
                        "baseline": baseline,
                        "health_factor": round(health_factor, 3),
                        "latency_factor": round(latency_factor, 3),
                        "adjusted_priority": adjusted,
                        "category": category,
                    }

        except Exception as e:
            logger.error(f"[PriorityAdjuster] Adjust failed: {e}")

        return results

    def get_adjustment_status(self) -> Dict[str, Any]:
        """获取调整器状态"""
        return {
            "running": self._running,
            "last_adjusted": dict(self._last_adjusted),
            "tracked_sources": list(self._health_history.keys()),
        }

    def _record_health(self, source_code: str, health_data: Dict[str, Any]):
        """记录健康检查结果"""
        if source_code not in self._health_history:
            self._health_history[source_code] = []

        self._health_history[source_code].append({
            "status": health_data.get("status", "unknown"),
            "latency_ms": health_data.get("latency_ms", 0),
            "ts": time.time(),
        })

        # 只保留最近 20 条
        if len(self._health_history[source_code]) > 20:
            self._health_history[source_code] = self._health_history[source_code][-20:]

    def _get_health_stats(self, source_code: str) -> Dict[str, Any]:
        """获取健康统计"""
        history = self._health_history.get(source_code, [])
        if not history:
            return {"healthy": 0, "degraded": 0, "unhealthy": 0, "avg_latency_ms": 0}

        healthy = sum(1 for h in history if h["status"] == "healthy")
        degraded = sum(1 for h in history if h["status"] in ("degraded", "empty_response"))
        unhealthy = sum(1 for h in history if h["status"] in ("unhealthy", "no_method"))

        latencies = [h["latency_ms"] for h in history if h["latency_ms"] > 0]
        avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

        return {
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "avg_latency_ms": avg_latency,
        }

    def _get_health_results(self) -> Dict[str, Dict[str, Any]]:
        """从健康检查器获取最新结果"""
        try:
            from app.services.data_source_health_checker import get_health_checker
            checker = get_health_checker()
            return checker.get_last_results()
        except Exception:
            return {}

    def _write_priority_log(
        self,
        source_code: str,
        category: str,
        baseline: float,
        adjusted: float,
        health_factor: float,
        latency_factor: float,
        stats: Dict[str, Any],
    ):
        """将优先级调整记录写入数据库"""
        try:
            import json
            from app.utils.db_postgres import execute_sql
            execute_sql(
                """INSERT INTO data_source_priority_log
                   (source_code, category, baseline_priority, adjusted_priority,
                    health_factor, latency_factor, avg_latency_ms, health_stats)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    source_code,
                    category,
                    baseline,
                    adjusted,
                    round(health_factor, 3),
                    round(latency_factor, 3),
                    stats.get("avg_latency_ms", 0),
                    json.dumps(stats),
                ),
                fetch=None,
            )
        except Exception as e:
            logger.debug(f"[PriorityAdjuster] DB log write failed for {source_code}: {e}")

    def _run_loop(self):
        """后台循环调整"""
        # 初始延迟
        self._stop_event.wait(60)

        while not self._stop_event.is_set():
            try:
                self.adjust_now()
            except Exception as e:
                logger.error(f"[PriorityAdjuster] Loop error: {e}")

            self._stop_event.wait(self.adjust_interval)


# ============================================
# 全局实例
# ============================================

_adjuster: Optional[PriorityAdjuster] = None
_adjuster_lock = threading.Lock()


def get_priority_adjuster() -> PriorityAdjuster:
    """获取全局优先级调整器实例"""
    global _adjuster
    if _adjuster is None:
        with _adjuster_lock:
            if _adjuster is None:
                _adjuster = PriorityAdjuster()
    return _adjuster


def start_priority_adjuster(adjust_interval: int = DEFAULT_ADJUST_INTERVAL):
    """启动优先级调整器"""
    global _adjuster
    with _adjuster_lock:
        if _adjuster is None:
            _adjuster = PriorityAdjuster(adjust_interval=adjust_interval)
        _adjuster.start()


def stop_priority_adjuster():
    """停止优先级调整器"""
    global _adjuster
    if _adjuster is not None:
        _adjuster.stop()
