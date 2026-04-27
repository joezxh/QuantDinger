"""Persist strategy runtime lines for the strategy management UI (`qd_strategy_logs`)."""
from __future__ import annotations

from app.database.repositories.runtime_ops_repository import RuntimeOpsRepository
from app.database.session import get_session
from app.utils.logger import get_logger

logger = get_logger(__name__)


def append_strategy_log(strategy_id: int, level: str, message: str) -> None:
    try:
        sid = int(strategy_id)
        lv = (level or "info").strip().lower()[:20]
        msg = str(message or "").strip()
        if not msg:
            return
        msg = msg[:8000]
        with get_session() as session:
            RuntimeOpsRepository(session).add_strategy_log(sid, lv, msg)
    except Exception as e:
        logger.debug("append_strategy_log skip: %s", e)
