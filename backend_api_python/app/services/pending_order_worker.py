"""Pending order worker.

This worker polls `pending_orders` periodically and dispatches orders based on `execution_mode`.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

from app.database.repositories.portfolio_repository import PendingOrderRepository, PortfolioRepository
from app.database.session import get_session
from app.services.signal_notifier import SignalNotifier
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PendingOrderWorker:
    def __init__(self, poll_interval_sec: float = 1.0, batch_size: int = 50):
        self.poll_interval_sec = float(poll_interval_sec)
        self.batch_size = int(batch_size)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._notifier = SignalNotifier()

    def start(self) -> bool:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return True
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name="PendingOrderWorker", daemon=True)
            self._thread.start()
            logger.info("PendingOrderWorker started")
            return True

    def stop(self, timeout_sec: float = 5.0) -> None:
        with self._lock:
            self._stop_event.set()
            th = self._thread
        if th and th.is_alive():
            th.join(timeout=timeout_sec)
        logger.info("PendingOrderWorker stopped")

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                logger.warning(f"PendingOrderWorker tick error: {e}")
            time.sleep(self.poll_interval_sec)

    def _tick(self) -> None:
        orders = self._fetch_pending_orders(limit=self.batch_size)
        if not orders:
            return
        for order in orders:
            oid = order.get("id")
            if not oid:
                continue
            if not self._mark_processing(order_id=int(oid)):
                continue
            try:
                self._dispatch_one(order)
            except Exception as e:
                self._mark_failed(order_id=int(oid), error=str(e))

    def _fetch_pending_orders(self, limit: int = 50):
        with get_session() as session:
            rows = PendingOrderRepository(session).list_pending_orders(limit=limit)
        return [
            {
                'id': row.id,
                'strategy_id': row.strategy_id,
                'symbol': row.symbol,
                'side': row.side,
                'status': row.status,
                'payload_json': row.payload_json,
            }
            for row in rows
        ]

    def _mark_processing(self, order_id: int):
        with get_session() as session:
            return PendingOrderRepository(session).mark_processing(order_id)

    def _mark_failed(self, order_id: int, error: str):
        with get_session() as session:
            return PendingOrderRepository(session).mark_failed(order_id, error)

    def _dispatch_one(self, order):
        logger.info(f"Dispatch pending order: {order.get('id')}")
        with get_session() as session:
            PendingOrderRepository(session).delete_order(int(order.get('id')))
