import json
import time
from typing import List, Dict, Any, Optional

from app.database.session import get_session
from app.database.repositories.llm_repository import LLmRepository
from app.utils.crypto import crypto_utils
from app.utils.logger import get_logger
from app.services.llm_lb import LLMNode

logger = get_logger(__name__)


class LLMRegistry:
    """
    Registry for LLM Providers, Models and API Keys.
    Handles database operations via SQLAlchemy ORM.
    """

    @classmethod
    def get_available_nodes(cls, model_name: str, user_id: int = 0) -> List[LLMNode]:
        """
        Get all available API keys for a specific model, considering permissions.
        """
        try:
            with get_session() as session:
                repo = LLmRepository(session)
                model_info = repo.get_model_by_name(model_name)
                if not model_info:
                    return []

                keys = repo.list_keys_for_model(model_name, user_id)

                nodes = []
                for key in keys:
                    node = LLMNode(key.id, key.weight)
                    node.fail_count = key.fail_count or 0
                    node.is_circuit_breaker_open = (key.status == 2)
                    nodes.append(node)

                return nodes
        except Exception as e:
            logger.error(f"get_available_nodes failed: {e}")
            return []

    @classmethod
    def get_node_details(cls, key_id: int) -> Dict[str, Any]:
        """Get full details of a node including decrypted API key and provider info"""
        try:
            with get_session() as session:
                repo = LLmRepository(session)
                row = repo.get_key_details(key_id)
                if row:
                    row['api_key'] = crypto_utils.decrypt(row['api_key_enc'])
                    return row
                return {}
        except Exception as e:
            logger.error(f"get_node_details failed: {e}")
            return {}

    @classmethod
    def get_model_config(cls, model_name: str) -> Dict[str, Any]:
        """Get LB strategy and other configs for a model"""
        try:
            with get_session() as session:
                repo = LLmRepository(session)
                return repo.get_model_config(model_name)
        except Exception as e:
            logger.error(f"get_model_config failed: {e}")
            return {}

    @classmethod
    def record_call_result(cls, key_id: int, model_id: int, user_id: int,
                           latency_ms: int, status_code: int, error_msg: str = None,
                           prompt_tokens: int = 0, completion_tokens: int = 0):
        """Record call metrics and update node status"""
        try:
            with get_session() as session:
                repo = LLmRepository(session)
                repo.record_call_result(
                    key_id=key_id,
                    model_id=model_id,
                    user_id=user_id,
                    latency_ms=latency_ms,
                    status_code=status_code,
                    error_msg=error_msg,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

                is_success = (200 <= status_code < 300)

                # Check for circuit breaker (via repo already handled in record_call_result)
                if not is_success:
                    key = repo.get_key_by_id(key_id)
                    if key and key.fail_count >= 5:
                        logger.warning(
                            f"Circuit breaker OPEN for API Key ID {key_id} "
                            f"due to {key.fail_count} consecutive failures."
                        )
        except Exception as e:
            logger.error(f"record_call_result failed: {e}")

    @classmethod
    def log_call(cls, key_id: int, model_id: int, user_id: int, latency_ms: int, status_code: int, error_msg: str = None):
        """Simplified log call for backward compatibility or quick use"""
        cls.record_call_result(key_id, model_id, user_id, latency_ms, status_code, error_msg)
