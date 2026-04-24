import json
import time
from typing import List, Dict, Any, Optional
from app.utils.db import get_db_connection
from app.utils.crypto import crypto_utils
from app.utils.logger import get_logger
from app.services.llm_lb import LLMNode

logger = get_logger(__name__)

class LLMRegistry:
    """
    Registry for LLM Providers, Models and API Keys.
    Handles database operations and caching.
    """
    
    @classmethod
    def get_available_nodes(cls, model_name: str, user_id: int = 0) -> List[LLMNode]:
        """
        Get all available API keys for a specific model, considering permissions.
        """
        try:
            with get_db_connection() as db:
                cur = db.cursor()
                # 1. Find the model and its strategy
                cur.execute(
                    """
                    SELECT m.id, m.lb_strategy, m.retries, m.timeout, p.code as provider_code
                    FROM qd_llm_model m
                    JOIN qd_llm_provider p ON m.provider_id = p.id
                    WHERE m.model_name = ? AND m.status = 1 AND p.status = 1
                    """,
                    (model_name,)
                )
                model_info = cur.fetchone()
                if not model_info:
                    return []

                # 2. Find all valid API keys for this provider
                # Filter by permission: is_public=1 OR owner_id=user_id
                cur.execute(
                    """
                    SELECT id, api_key_enc, weight, status, fail_count, last_used_at, metrics
                    FROM qd_llm_api_key
                    WHERE provider_id = (SELECT provider_id FROM qd_llm_model WHERE model_name = ? LIMIT 1)
                      AND status != 0
                      AND (is_public = 1 OR owner_id = ?)
                    """,
                    (model_name, user_id)
                )
                rows = cur.fetchall()
                cur.close()

                nodes = []
                for row in rows:
                    node = LLMNode(row['id'], row['weight'])
                    node.fail_count = row['fail_count'] or 0
                    node.is_circuit_breaker_open = (row['status'] == 2)
                    
                    # Decrypt key for later use (done in service, not here to avoid leaks in registry)
                    # node.decrypted_key = crypto_utils.decrypt(row['api_key_enc'])
                    
                    nodes.append(node)
                
                return nodes
        except Exception as e:
            logger.error(f"get_available_nodes failed: {e}")
            return []

    @classmethod
    def get_node_details(cls, key_id: int) -> Dict[str, Any]:
        """Get full details of a node including decrypted API key and provider info"""
        try:
            with get_db_connection() as db:
                cur = db.cursor()
                cur.execute(
                    """
                    SELECT k.*, p.base_url, p.api_type, p.code as provider_code
                    FROM qd_llm_api_key k
                    JOIN qd_llm_provider p ON k.provider_id = p.id
                    WHERE k.id = ?
                    """,
                    (key_id,)
                )
                row = cur.fetchone()
                cur.close()
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
            with get_db_connection() as db:
                cur = db.cursor()
                cur.execute(
                    "SELECT * FROM qd_llm_model WHERE model_name = ? AND status = 1",
                    (model_name,)
                )
                row = cur.fetchone()
                cur.close()
                return row or {}
        except Exception as e:
            logger.error(f"get_model_config failed: {e}")
            return {}

    @classmethod
    def record_call_result(cls, key_id: int, model_id: int, user_id: int, 
                           latency_ms: int, status_code: int, error_msg: str = None,
                           prompt_tokens: int = 0, completion_tokens: int = 0):
        """Record call metrics and update node status"""
        try:
            with get_db_connection() as db:
                cur = db.cursor()
                # 1. Insert log
                cur.execute(
                    """
                    INSERT INTO qd_llm_call_log 
                    (api_key_id, model_id, user_id, prompt_tokens, completion_tokens, total_tokens, latency_ms, status_code, error_msg)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (key_id, model_id, user_id, prompt_tokens, completion_tokens, prompt_tokens + completion_tokens, latency_ms, status_code, error_msg)
                )

                # 2. Update key stats
                is_success = (200 <= status_code < 300)
                if is_success:
                    cur.execute(
                        """
                        UPDATE qd_llm_api_key 
                        SET fail_count = 0, status = 1, last_used_at = NOW(), 
                            updated_at = NOW()
                        WHERE id = ?
                        """,
                        (key_id,)
                    )
                else:
                    cur.execute(
                        """
                        UPDATE qd_llm_api_key 
                        SET fail_count = fail_count + 1, last_used_at = NOW(),
                            updated_at = NOW()
                        WHERE id = ?
                        """,
                        (key_id,)
                    )
                    
                    # 3. Check for circuit breaker (e.g. 5 consecutive failures)
                    cur.execute("SELECT fail_count FROM qd_llm_api_key WHERE id = ?", (key_id,))
                    row = cur.fetchone()
                    if row and row['fail_count'] >= 5:
                        cur.execute("UPDATE qd_llm_api_key SET status = 2 WHERE id = ?", (key_id,))
                        logger.warning(f"Circuit breaker OPEN for API Key ID {key_id} due to 5 consecutive failures.")

                db.commit()
                cur.close()
        except Exception as e:
            logger.error(f"record_call_result failed: {e}")

    @classmethod
    def log_call(cls, key_id: int, model_id: int, user_id: int, latency_ms: int, status_code: int, error_msg: str = None):
        """Simplified log call for backward compatibility or quick use"""
        cls.record_call_result(key_id, model_id, user_id, latency_ms, status_code, error_msg)
