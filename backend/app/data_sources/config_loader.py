"""
数据源配置加载器
从数据库读取数据源配置、API密钥和限流参数
"""
import os
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.utils.logger import get_logger

logger = get_logger(__name__)


class DataSourceConfigLoader:
    """
    数据源配置加载器
    
    从数据库加载数据源配置，替换原有的环境变量读取方式
    支持回退到环境变量作为兼容方案
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def load_source_config(self, source_code: str) -> Optional[Dict[str, Any]]:
        """
        加载指定数据源的完整配置

        Args:
            source_code: 数据源代码 (如 'crypto_ccxt')

        Returns:
            完整配置字典，包含API地址、密钥、限流参数等
        """
        try:
            from app.models.data_source_meta import (
                DataSourceConfig,
                DataSourceRateLimitConfig,
                ApiKey
            )

            # 1. 加载数据源基本配置
            source_config = self.db_session.query(DataSourceConfig).filter(
                DataSourceConfig.source_code == source_code
            ).first()

            if not source_config:
                logger.warning(f"未找到数据源配置: {source_code}")
                return self._get_fallback_config(source_code)

            config = {
                'source_code': source_config.source_code,
                'source_name': source_config.source_name,
                'layer': source_config.layer,
                'market_categories': source_config.market_categories or [],
                'enabled': source_config.enabled,
                'load_balance_strategy': source_config.load_balance_strategy,
                'config_json': source_config.config_json or {},
                'dependencies': source_config.dependencies or [],
            }

            # 2. 加载限流配置
            rate_limit = self.db_session.query(DataSourceRateLimitConfig).filter(
                DataSourceRateLimitConfig.source_config_id == source_config.id,
                DataSourceRateLimitConfig.enabled == True
            ).first()

            if rate_limit:
                config['rate_limit'] = {
                    'strategy': rate_limit.strategy,
                    'rate': rate_limit.rate,
                    'period': rate_limit.period,
                    'burst': rate_limit.burst or rate_limit.rate,
                    'max_concurrent': rate_limit.max_concurrent,
                    'enable_adaptive': rate_limit.enable_adaptive,
                    'min_rate': rate_limit.min_rate,
                    'max_rate': rate_limit.max_rate,
                    'reduce_rate_on_error': rate_limit.reduce_rate_on_error,
                    'error_threshold': rate_limit.error_threshold,
                    'priority': rate_limit.priority,
                    'weight': rate_limit.weight,
                }
            else:
                # 使用默认限流配置
                config['rate_limit'] = self._get_default_rate_limit(source_code)

            # 3. 加载API密钥
            api_keys = self.db_session.query(ApiKey).filter(
                ApiKey.source_config_id == source_config.id,
                ApiKey.status == 'active'
            ).all()

            if api_keys:
                config['api_keys'] = [
                    {
                        'id': key.id,
                        'key_type': key.key_type,
                        'key_alias': key.key_alias,
                        'weight': key.weight,
                        'daily_call_limit': key.daily_call_limit,
                        'current_daily_calls': key.current_daily_calls,
                        'consecutive_errors': key.consecutive_errors,
                        'total_calls': key.total_calls,
                    }
                    for key in api_keys
                ]

            return config

        except Exception as e:
            logger.error(f"加载数据源配置失败: {source_code}, 错误: {e}")
            return self._get_fallback_config(source_code)

    def get_api_key(self, source_code: str, key_type: str = 'public') -> Optional[str]:
        """
        获取数据源的API密钥（解密后）

        Args:
            source_code: 数据源代码
            key_type: 密钥类型 (public/private)

        Returns:
            解密后的API密钥字符串，或None
        """
        try:
            from app.models.data_source_meta import DataSourceConfig, ApiKey
            from app.utils.crypto import CryptoUtils

            # 查找数据源配置
            source_config = self.db_session.query(DataSourceConfig).filter(
                DataSourceConfig.source_code == source_code
            ).first()

            if not source_config:
                return None

            # 查找API密钥
            api_key = self.db_session.query(ApiKey).filter(
                ApiKey.source_config_id == source_config.id,
                ApiKey.key_type == key_type,
                ApiKey.status == 'active'
            ).first()

            if not api_key:
                # 回退到环境变量
                env_var = source_config.config_json.get('api_key_env')
                if env_var:
                    return os.environ.get(env_var)
                return None

            # 解密API密钥
            decrypted_key = CryptoUtils.decrypt(api_key.encrypted_key_value)
            return decrypted_key

        except Exception as e:
            logger.error(f"获取API密钥失败: {source_code}, 错误: {e}")
            return None

    def load_all_enabled_sources(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        加载所有启用的数据源配置

        Args:
            category: 可选，按市场类别过滤 (如 'Crypto', 'USStock')

        Returns:
            数据源配置列表
        """
        try:
            from app.models.data_source_meta import DataSourceConfig

            query = self.db_session.query(DataSourceConfig).filter(
                DataSourceConfig.enabled == True
            )

            if category:
                # 过滤包含指定类别的数据源
                query = query.filter(
                    DataSourceConfig.market_categories.contains([category])
                )

            sources = query.all()

            configs = []
            for source in sources:
                config = self.load_source_config(source.source_code)
                if config:
                    configs.append(config)

            return configs

        except Exception as e:
            logger.error(f"加载所有数据源配置失败: {e}")
            return []

    def _get_fallback_config(self, source_code: str) -> Optional[Dict[str, Any]]:
        """
        回退配置：从环境变量读取（向后兼容）

        Args:
            source_code: 数据源代码

        Returns:
            从环境变量构建的配置字典
        """
        # 定义环境变量到数据源的映射
        env_mappings = {
            'crypto_ccxt': {
                'api_key_env': 'CCXT_API_KEY',
                'timeout_sec': int(os.environ.get('CCXT_TIMEOUT', '10000')),
                'rate_limit_per_min': 60,
            },
            'us_stock_finnhub': {
                'api_key_env': 'FINNHUB_API_KEY',
                'timeout_sec': int(os.environ.get('FINNHUB_TIMEOUT', '10')),
                'rate_limit_per_min': int(os.environ.get('FINNHUB_RATE_LIMIT', '60')),
            },
            'us_stock_tiingo': {
                'api_key_env': 'TIINGO_API_KEY',
                'timeout_sec': int(os.environ.get('TIINGO_TIMEOUT', '30')),
                'rate_limit_per_min': 60,
            },
            'twelve_data': {
                'api_key_env': 'TWELVE_DATA_API_KEY',
                'timeout_sec': 15,
                'rate_limit_per_min': 8,
            },
            'crypto_coinglass': {
                'api_key_env': 'COINGLASS_API_KEY',
                'timeout_sec': 15,
                'rate_limit_per_min': 60,
            },
            'crypto_quant': {
                'api_key_env': 'CRYPTOQUANT_API_KEY',
                'timeout_sec': 15,
                'rate_limit_per_min': 60,
            },
        }

        if source_code not in env_mappings:
            return None

        mapping = env_mappings[source_code]
        api_key = os.environ.get(mapping['api_key_env'])

        if not api_key:
            logger.debug(f"环境变量未配置: {mapping['api_key_env']}")
            return None

        return {
            'source_code': source_code,
            'api_key': api_key,
            'config_json': {
                'api_key_env': mapping['api_key_env'],
                'timeout_sec': mapping['timeout_sec'],
            },
            'rate_limit': self._get_default_rate_limit(source_code),
        }

    def _get_default_rate_limit(self, source_code: str) -> Dict[str, Any]:
        """
        获取默认限流配置

        Args:
            source_code: 数据源代码

        Returns:
            限流配置字典
        """
        from app.data_sources.token_bucket_limiter import _DEFAULT_LIMITER_CONFIGS

        config = _DEFAULT_LIMITER_CONFIGS.get(source_code, {"rate": 60, "period": 60})

        return {
            'strategy': 'token_bucket',
            'rate': config['rate'],
            'period': config['period'],
            'burst': config['rate'],
            'max_concurrent': 10,
            'enable_adaptive': False,
            'reduce_rate_on_error': True,
            'error_threshold': 5,
            'priority': 50,
            'weight': 1,
        }


def get_config_loader(db_session: Session) -> DataSourceConfigLoader:
    """
    获取配置加载器实例

    Args:
        db_session: 数据库会话

    Returns:
        DataSourceConfigLoader 实例
    """
    return DataSourceConfigLoader(db_session)
