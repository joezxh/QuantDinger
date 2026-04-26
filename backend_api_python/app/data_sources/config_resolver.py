"""
数据源配置解析器
从数据库配置表中读取数据源配置和 API 密钥，替代环境变量方式。
支持向后兼容：当数据库中无配置时，自动回退到环境变量。
"""
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.database.session import get_session
from app.models.data_source_meta import DataSourceConfig, ApiKey
from app.utils.crypto import CryptoUtils
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigResolver:
    """
    数据源配置解析器
    
    统一从 data_data_source_configs + data_api_keys 表读取配置。
    向后兼容：如果表中没有配置，回退到环境变量 / config_loader。
    """

    # source_code 到环境变量回退配置的映射
    _FALLBACK_CONFIGS = {
        "crypto_ccxt": {
            "config_json": {
                "default_exchange": os.getenv("CCXT_DEFAULT_EXCHANGE", "binance"),
                "timeout_sec": int(os.getenv("CCXT_TIMEOUT", "10000")) // 1000,
                "enable_rate_limit": True,
                "proxy": os.getenv("PROXY_URL", ""),
            }
        },
        "us_stock_finnhub": {
            "config_json": {
                "base_url": "https://finnhub.io/api/v1",
                "timeout_sec": int(os.getenv("FINNHUB_TIMEOUT", "10")),
                "rate_limit_per_min": int(os.getenv("FINNHUB_RATE_LIMIT", "60")),
            }
        },
        "us_stock_tiingo": {
            "config_json": {
                "base_url": "https://api.tiingo.com/tiingo",
                "timeout_sec": int(os.getenv("TIINGO_TIMEOUT", "10")),
            }
        },
        "forex_twelve_data": {
            "config_json": {
                "base_url": "https://api.twelvedata.com",
                "timeout_sec": 20,
            }
        },
        "forex_tiingo": {
            "config_json": {
                "base_url": "https://api.tiingo.com/tiingo",
                "timeout_sec": int(os.getenv("TIINGO_TIMEOUT", "10")),
            }
        },
        "futures_twelve_data": {
            "config_json": {
                "base_url": "https://api.twelvedata.com",
                "timeout_sec": 20,
            }
        },
        "futures_tiingo": {
            "config_json": {
                "base_url": "https://api.tiingo.com/tiingo",
                "timeout_sec": int(os.getenv("TIINGO_TIMEOUT", "10")),
            }
        },
        "hk_stock_twelve_data": {
            "config_json": {
                "base_url": "https://api.twelvedata.com",
                "timeout_sec": 20,
            }
        },
        "cn_stock_akshare": {
            "config_json": {
                "timeout_sec": int(os.getenv("AKSHARE_TIMEOUT", "30")),
            }
        },
    }

    @classmethod
    def get_source_config(cls, source_code: str) -> Optional[Dict[str, Any]]:
        """
        获取数据源配置
        
        Args:
            source_code: 数据源代码，如 'crypto_ccxt', 'us_stock_finnhub'
            
        Returns:
            配置字典，包含 config_json 等字段；如数据库中无配置则回退到环境变量
        """
        try:
            with get_session() as session:
                config = session.query(DataSourceConfig).filter(
                    DataSourceConfig.source_code == source_code
                ).first()
                if config:
                    return {
                        "id": config.id,
                        "source_code": config.source_code,
                        "source_name": config.source_name,
                        "layer": config.layer,
                        "market_categories": config.market_categories,
                        "enabled": config.enabled,
                        "load_balance_strategy": config.load_balance_strategy,
                        "config_json": config.config_json or {},
                        "dependencies": config.dependencies,
                    }
        except Exception as e:
            logger.warning(
                f"Failed to read config from DB for {source_code}: {e}. "
                f"Falling back to environment variables."
            )

        # 回退到环境变量
        fallback = cls._FALLBACK_CONFIGS.get(source_code, {})
        fallback["source_code"] = source_code
        fallback["enabled"] = True
        fallback["load_balance_strategy"] = "round_robin"
        fallback["config_json"] = fallback.get("config_json", {})
        logger.debug(f"Using fallback config for {source_code}")
        return fallback

    @classmethod
    def get_api_key(
        cls,
        source_code: str,
        key_type: str = "public",
        user_id: Optional[int] = None,
        strategy: Optional[str] = None
    ) -> Optional[str]:
        """
        获取 API 密钥值
        
        Args:
            source_code: 数据源代码
            key_type: 'public' 或 'private'
            user_id: 用户ID（用于 private 密钥）
            strategy: 负载均衡策略，默认使用配置中的策略
            
        Returns:
            解密的 API 密钥字符串，或 None
        """
        # 先尝试从数据库读取
        try:
            with get_session() as session:
                config = session.query(DataSourceConfig).filter(
                    DataSourceConfig.source_code == source_code
                ).first()
                if not config:
                    raise ValueError(f"Config not found for {source_code}")

                # 查询可用密钥
                query = session.query(ApiKey).filter(
                    ApiKey.source_config_id == config.id,
                    ApiKey.status == "active"
                )

                if key_type == "private" and user_id:
                    # 优先查找用户的 private 密钥
                    private_key = query.filter(
                        ApiKey.key_type == "private",
                        ApiKey.user_id == user_id
                    ).first()
                    if private_key:
                        return CryptoUtils.decrypt(private_key.encrypted_key_value)
                    # 如果没有 private 密钥，回退到 public
                    query = session.query(ApiKey).filter(
                        ApiKey.source_config_id == config.id,
                        ApiKey.status == "active",
                        ApiKey.key_type == "public"
                    )
                else:
                    query = query.filter(ApiKey.key_type == "public")

                keys = query.all()
                if not keys:
                    raise ValueError(f"No active API keys found for {source_code}")

                # 应用负载均衡策略
                strategy = strategy or config.load_balance_strategy or "round_robin"
                selected = cls._select_key(keys, strategy)
                if selected:
                    # 更新调用计数
                    selected.current_daily_calls += 1
                    selected.total_calls += 1
                    session.flush()
                    return CryptoUtils.decrypt(selected.encrypted_key_value)

        except Exception as e:
            logger.warning(
                f"Failed to read API key from DB for {source_code}: {e}. "
                f"Falling back to environment variables."
            )

        # 回退到环境变量
        return cls._get_fallback_api_key(source_code)

    @classmethod
    def get_all_keys_for_source(
        cls,
        source_code: str,
        key_type: str = "public"
    ) -> list[str]:
        """获取某个数据源的所有可用密钥（用于轮询/容错）"""
        try:
            with get_session() as session:
                config = session.query(DataSourceConfig).filter(
                    DataSourceConfig.source_code == source_code
                ).first()
                if not config:
                    return []

                keys = session.query(ApiKey).filter(
                    ApiKey.source_config_id == config.id,
                    ApiKey.status == "active",
                    ApiKey.key_type == key_type
                ).all()

                return [CryptoUtils.decrypt(k.encrypted_key_value) for k in keys]
        except Exception as e:
            logger.warning(f"Failed to read keys from DB for {source_code}: {e}")
            fallback = cls._get_fallback_api_key(source_code)
            return [fallback] if fallback else []

    @classmethod
    def _select_key(cls, keys: list, strategy: str) -> Optional[ApiKey]:
        """应用负载均衡策略选择密钥"""
        import random

        if not keys:
            return None

        # 过滤掉超过日调用限制的密钥
        valid_keys = [
            k for k in keys
            if k.daily_call_limit == 0 or k.current_daily_calls < k.daily_call_limit
        ]
        if not valid_keys:
            return None

        if strategy == "random":
            return random.choice(valid_keys)

        if strategy == "health_first":
            return min(valid_keys, key=lambda k: k.consecutive_errors)

        if strategy == "weighted":
            total_weight = sum(k.weight for k in valid_keys)
            if total_weight == 0:
                return random.choice(valid_keys)
            pick = random.uniform(0, total_weight)
            current = 0
            for key in valid_keys:
                current += key.weight
                if current >= pick:
                    return key
            return valid_keys[-1]

        # round_robin: 选择总调用数最少的
        return min(valid_keys, key=lambda k: k.total_calls)

    @classmethod
    def _get_fallback_api_key(cls, source_code: str) -> Optional[str]:
        """从环境变量获取 API 密钥（向后兼容）"""
        env_map = {
            "us_stock_finnhub": "FINNHUB_API_KEY",
            "us_stock_tiingo": "TIINGO_API_KEY",
            "forex_twelve_data": "TWELVE_DATA_API_KEY",
            "futures_twelve_data": "TWELVE_DATA_API_KEY",
            "hk_stock_twelve_data": "TWELVE_DATA_API_KEY",
        }
        env_key = env_map.get(source_code)
        if env_key:
            val = os.getenv(env_key, "").strip()
            if val:
                return val
        return None

    @classmethod
    def report_key_error(cls, source_code: str, key_value: str) -> None:
        """报告密钥调用错误，用于健康检查"""
        try:
            with get_session() as session:
                config = session.query(DataSourceConfig).filter(
                    DataSourceConfig.source_code == source_code
                ).first()
                if not config:
                    return
                # 查找匹配的密钥（通过加密值匹配不安全，这里简化处理）
                # 实际使用中建议通过 key_id 报告
                keys = session.query(ApiKey).filter(
                    ApiKey.source_config_id == config.id,
                    ApiKey.status == "active"
                ).all()
                for k in keys:
                    try:
                        decrypted = CryptoUtils.decrypt(k.encrypted_key_value)
                        if decrypted == key_value:
                            k.consecutive_errors += 1
                            k.last_error_at = datetime.now(timezone.utc)
                            if k.consecutive_errors >= k.max_consecutive_errors:
                                k.status = "error"
                                logger.warning(
                                    f"API key {k.id} disabled after "
                                    f"{k.consecutive_errors} consecutive errors"
                                )
                            session.flush()
                            break
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"report_key_error failed: {e}")


# 保持向后兼容的快捷导入
resolve_config = ConfigResolver.get_source_config
resolve_api_key = ConfigResolver.get_api_key
