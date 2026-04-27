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

    def list_strategies(self, user_id: int) -> List[Dict[str, Any]]:
        """List strategies for a specific user"""
        from sqlalchemy import select
        from app.models.strategy import StrategyTrading
        try:
            with get_session() as session:
                stmt = select(StrategyTrading).where(StrategyTrading.user_id == user_id).order_by(StrategyTrading.id.desc())
                rows = session.execute(stmt).scalars().all()
                strategies = []
                repo = StrategyRepository(session)
                for row in rows:
                    config = repo.load_strategy_config(row.id)
                    if config:
                        config['created_at'] = str(row.created_at) if row.created_at else None
                        strategies.append(config)
                return strategies
        except Exception as e:
            logger.error(f"Failed to fetch strategies for user {user_id}: {str(e)}")
            return []

    def get_strategy(self, strategy_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific strategy by ID for a user"""
        try:
            with get_session() as session:
                repo = StrategyRepository(session)
                strategy = repo.get_by_id(strategy_id)
                if not strategy or strategy.user_id != user_id:
                    return None
                config = repo.load_strategy_config(strategy_id)
                if config:
                    config['created_at'] = str(strategy.created_at) if strategy.created_at else None
                return config
        except Exception as e:
            logger.error(f"Failed to fetch strategy {strategy_id} for user {user_id}: {str(e)}")
            return None

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
