import os
import time
import json
import threading
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database.repositories.strategy_repository import StrategyRepository
from app.database.session import get_session
from app.utils.logger import get_logger


logger = get_logger(__name__)


class StrategyService:
    """Strategy service."""

    _connection_test_semaphore = threading.Semaphore(5)

    def __init__(self):
        pass

    def get_running_strategies(self) -> List[Dict[str, Any]]:
        """Get all running strategies (ID only)"""
        try:
            with get_session() as session:
                rows = StrategyRepository(session).list_running_strategies()
                return [row.id for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch running strategies: {str(e)}")
            return []

    def get_running_strategies_with_type(self) -> List[Dict[str, Any]]:
        """Get all running strategies (with type info)"""
        try:
            with get_session() as session:
                rows = StrategyRepository(session).list_running_strategies()
                strategies = [{'id': row.id, 'strategy_type': getattr(row, 'strategy_type', '') or ''} for row in rows]
                logger.info(f"Found {len(strategies)} running strategies: {strategies}")
                return strategies
        except Exception as e:
            logger.error(f"Failed to fetch running strategies: {str(e)}")
            return []
