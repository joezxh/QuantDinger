"""Strategy repository helpers."""
import json
from datetime import datetime
from sqlalchemy import select, update, func

from app.database.repositories.base import BaseRepository
from app.models.strategy import StrategyTrading


class StrategyRepository(BaseRepository):
    def list_running_strategies(self):
        stmt = select(StrategyTrading).where(StrategyTrading.status == "running")
        return list(self.session.execute(stmt).scalars())

    def get_by_id(self, strategy_id: int):
        return self.session.get(StrategyTrading, strategy_id)

    def get_status(self, strategy_id: int) -> str:
        stmt = select(StrategyTrading.status).where(StrategyTrading.id == strategy_id)
        return self.session.execute(stmt).scalar() or ""

    def set_status(self, strategy_id: int, status: str):
        strategy = self.get_by_id(strategy_id)
        if strategy:
            strategy.status = status
            self.flush()
            return True
        return False

    def load_strategy_config(self, strategy_id: int) -> dict | None:
        """Load full strategy config with all fields."""
        strategy = self.get_by_id(strategy_id)
        if not strategy:
            return None
        config = {
            'id': strategy.id,
            'strategy_name': strategy.strategy_name,
            'strategy_type': strategy.strategy_type,
            'status': strategy.status,
            'initial_capital': float(strategy.initial_capital) if strategy.initial_capital else 0,
            'leverage': strategy.leverage,
            'decide_interval': strategy.decide_interval,
            'execution_mode': strategy.execution_mode,
            'notification_config': strategy.notification_config,
            'indicator_config': strategy.indicator_config,
            'exchange_config': strategy.exchange_config,
            'trading_config': strategy.trading_config,
            'ai_model_config': strategy.ai_model_config,
            'market_category': strategy.market_category,
            'strategy_mode': strategy.strategy_mode,
            'strategy_code': strategy.strategy_code,
        }
        # Parse JSON fields
        for field in ['indicator_config', 'trading_config', 'notification_config', 'ai_model_config']:
            if isinstance(config.get(field), str):
                try:
                    config[field] = json.loads(config[field])
                except Exception:
                    config[field] = {}

        # exchange_config: parse JSON
        exchange_config_str = config.get('exchange_config', '{}')
        if isinstance(exchange_config_str, str) and exchange_config_str:
            try:
                config['exchange_config'] = json.loads(exchange_config_str)
            except Exception:
                config['exchange_config'] = {}
        else:
            config['exchange_config'] = exchange_config_str if isinstance(exchange_config_str, dict) else {}

        return config

    def get_trading_config(self, strategy_id: int) -> dict | None:
        strategy = self.get_by_id(strategy_id)
        if not strategy or not strategy.trading_config:
            return None
        tc = strategy.trading_config
        if isinstance(tc, str):
            try:
                tc = json.loads(tc)
            except Exception:
                tc = {}
        elif not isinstance(tc, dict):
            tc = {}
        return tc

    def update_trading_config(self, strategy_id: int, trading_config: dict):
        strategy = self.get_by_id(strategy_id)
        if strategy:
            strategy.trading_config = json.dumps(trading_config, ensure_ascii=False)
            self.flush()
            return True
        return False

    def get_last_rebalance(self, strategy_id: int):
        """Get last_rebalance_at timestamp for cross-sectional rebalance check."""
        strategy = self.get_by_id(strategy_id)
        if not strategy:
            return None
        return strategy.last_rebalance_at

    def update_last_rebalance(self, strategy_id: int):
        """Update last_rebalance_at to now."""
        strategy = self.get_by_id(strategy_id)
        if strategy:
            strategy.last_rebalance_at = func.now()
            self.flush()
            return True
        return False

    def get_user_id(self, strategy_id: int) -> int:
        """Get user_id for a strategy, defaults to 1."""
        strategy = self.get_by_id(strategy_id)
        if strategy:
            return strategy.user_id
        return 1

    def get_user_timezone(self, strategy_id: int) -> str:
        """Get user timezone for a strategy via user relationship."""
        strategy = self.get_by_id(strategy_id)
        if strategy and strategy.user:
            return str(strategy.user.timezone or "").strip()
        return ""
