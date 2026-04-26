"""
API 密钥管理服务
管理 ApiKey 的 CRUD、加密存储、负载均衡调度
"""
import random
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from app.database.session import get_session
from app.models.data_source_meta import ApiKey
from app.utils.crypto import CryptoUtils
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ApiKeyService:
    """API 密钥管理服务"""

    def list_keys(
        self,
        source_config_id: Optional[int] = None,
        key_type: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[int] = None,
        user_role: str = "user",
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """列出 API 密钥（带权限过滤）"""
        with get_session() as session:
            query = session.query(ApiKey)

            if source_config_id:
                query = query.filter(ApiKey.source_config_id == source_config_id)
            if key_type:
                query = query.filter(ApiKey.key_type == key_type)
            if status:
                query = query.filter(ApiKey.status == status)

            # 权限过滤：非管理员只能看到自己的 private 密钥和 public 密钥
            if user_role != "admin":
                if user_id:
                    query = query.filter(
                        (ApiKey.key_type == "public") |
                        ((ApiKey.key_type == "private") & (ApiKey.user_id == user_id))
                    )
                else:
                    query = query.filter(ApiKey.key_type == "public")

            total = query.count()
            items = query.order_by(ApiKey.id.desc()).offset(
                (page - 1) * page_size
            ).limit(page_size).all()

            return {
                "items": [self._to_dict(item, include_encrypted=False) for item in items],
                "total": total,
                "page": page,
                "page_size": page_size
            }

    def get_key(self, key_id: int, user_id: Optional[int] = None, user_role: str = "user") -> Optional[Dict[str, Any]]:
        """获取单个 API 密钥"""
        with get_session() as session:
            key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
            if not key:
                return None
            if not self._can_access(key, user_id, user_role):
                return None
            return self._to_dict(key, include_encrypted=False)

    def create_key(self, data: Dict[str, Any], created_by: Optional[int] = None) -> Dict[str, Any]:
        """创建 API 密钥"""
        raw_value = data.get("key_value", "").strip()
        if not raw_value:
            raise ValueError("API 密钥值不能为空")

        encrypted = CryptoUtils.encrypt(raw_value)
        hint = self._generate_hint(raw_value)

        with get_session() as session:
            key = ApiKey(
                source_config_id=data["source_config_id"],
                key_type=data.get("key_type", "public"),
                user_id=data.get("user_id"),
                key_alias=data.get("key_alias", ""),
                encrypted_key_value=encrypted,
                key_hint=hint,
                status=data.get("status", "active"),
                weight=data.get("weight", 1),
                max_consecutive_errors=data.get("max_consecutive_errors", 5),
                daily_call_limit=data.get("daily_call_limit", 0),
                created_by=created_by,
            )
            session.add(key)
            session.flush()
            logger.info(f"Created API key: id={key.id}, type={key.key_type}, source={key.source_config_id}")
            return self._to_dict(key, include_encrypted=False)

    def update_key(
        self, key_id: int, data: Dict[str, Any], user_id: Optional[int] = None, user_role: str = "user"
    ) -> Optional[Dict[str, Any]]:
        """更新 API 密钥"""
        with get_session() as session:
            key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
            if not key:
                return None
            if not self._can_modify(key, user_id, user_role):
                return None

            allowed_fields = [
                "key_alias", "status", "weight", "max_consecutive_errors",
                "daily_call_limit"
            ]
            for field in allowed_fields:
                if field in data:
                    setattr(key, field, data[field])

            # 如果提供了新的密钥值，重新加密
            if "key_value" in data and data["key_value"]:
                key.encrypted_key_value = CryptoUtils.encrypt(data["key_value"])
                key.key_hint = self._generate_hint(data["key_value"])

            # 管理员可以修改 key_type 和 user_id
            if user_role == "admin":
                if "key_type" in data:
                    key.key_type = data["key_type"]
                if "user_id" in data:
                    key.user_id = data["user_id"]

            session.flush()
            logger.info(f"Updated API key: id={key.id}")
            return self._to_dict(key, include_encrypted=False)

    def delete_key(self, key_id: int, user_id: Optional[int] = None, user_role: str = "user") -> bool:
        """删除 API 密钥"""
        with get_session() as session:
            key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
            if not key:
                return False
            if not self._can_modify(key, user_id, user_role):
                return False
            session.delete(key)
            logger.info(f"Deleted API key: id={key_id}")
            return True

    def decrypt_key_value(self, key_id: int, user_id: Optional[int] = None, user_role: str = "user") -> Optional[str]:
        """解密 API 密钥值（仅用于实际调用）"""
        with get_session() as session:
            key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
            if not key:
                return None
            if not self._can_access(key, user_id, user_role):
                return None
            try:
                return CryptoUtils.decrypt(key.encrypted_key_value)
            except Exception as e:
                logger.error(f"Failed to decrypt key {key_id}: {e}")
                return None

    def select_key_for_call(
        self,
        source_config_id: int,
        strategy: str = "round_robin",
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        为数据源调用选择一个可用的 API 密钥
        支持负载均衡策略：round_robin / weighted / health_first / random
        """
        with get_session() as session:
            query = session.query(ApiKey).filter(
                ApiKey.source_config_id == source_config_id,
                ApiKey.status == "active"
            )

            # 优先使用用户的 private 密钥，如果没有则使用 public 密钥
            if user_id:
                private_keys = query.filter(ApiKey.user_id == user_id).all()
                if private_keys:
                    keys = private_keys
                else:
                    keys = query.filter(ApiKey.key_type == "public").all()
            else:
                keys = query.filter(ApiKey.key_type == "public").all()

            if not keys:
                return None

            # 过滤掉超过日调用限制的密钥
            valid_keys = [
                k for k in keys
                if k.daily_call_limit == 0 or k.current_daily_calls < k.daily_call_limit
            ]
            if not valid_keys:
                return None

            selected = self._apply_strategy(valid_keys, strategy)
            if selected:
                # 更新调用计数
                selected.current_daily_calls += 1
                selected.total_calls += 1
                session.flush()
                return {
                    "id": selected.id,
                    "key_value": CryptoUtils.decrypt(selected.encrypted_key_value),
                    "key_alias": selected.key_alias,
                    "weight": selected.weight,
                }
            return None

    def report_error(self, key_id: int, error_message: str = "") -> None:
        """报告密钥调用错误，用于健康检查"""
        with get_session() as session:
            key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
            if not key:
                return
            key.consecutive_errors += 1
            key.last_error_at = datetime.now(timezone.utc)
            if key.consecutive_errors >= key.max_consecutive_errors:
                key.status = "error"
                logger.warning(
                    f"API key {key_id} disabled after {key.consecutive_errors} consecutive errors"
                )
            session.flush()

    def report_success(self, key_id: int) -> None:
        """报告密钥调用成功，重置错误计数"""
        with get_session() as session:
            key = session.query(ApiKey).filter(ApiKey.id == key_id).first()
            if not key:
                return
            if key.consecutive_errors > 0:
                key.consecutive_errors = 0
                if key.status == "error":
                    key.status = "active"
            session.flush()

    def reset_daily_counters(self) -> int:
        """重置所有密钥的日调用计数（应每日定时调用）"""
        with get_session() as session:
            count = session.query(ApiKey).update({
                "current_daily_calls": 0,
                "last_reset_at": datetime.now(timezone.utc)
            })
            logger.info(f"Reset daily counters for {count} API keys")
            return count

    def _apply_strategy(self, keys: List[ApiKey], strategy: str) -> Optional[ApiKey]:
        """应用负载均衡策略选择密钥"""
        if strategy == "random":
            return random.choice(keys)

        if strategy == "health_first":
            # 按连续错误数升序排列，优先选择错误少的
            sorted_keys = sorted(keys, key=lambda k: k.consecutive_errors)
            return sorted_keys[0]

        if strategy == "weighted":
            # 按权重加权随机选择
            total_weight = sum(k.weight for k in keys)
            if total_weight == 0:
                return random.choice(keys)
            pick = random.uniform(0, total_weight)
            current = 0
            for key in keys:
                current += key.weight
                if current >= pick:
                    return key
            return keys[-1]

        # round_robin: 选择总调用数最少的
        return min(keys, key=lambda k: k.total_calls)

    def _generate_hint(self, key_value: str) -> str:
        """生成密钥提示，如 ****a1b2"""
        if len(key_value) <= 4:
            return "****"
        return f"****{key_value[-4:]}"

    def _can_access(self, key: ApiKey, user_id: Optional[int], user_role: str) -> bool:
        """检查用户是否有权查看密钥"""
        if user_role == "admin":
            return True
        if key.key_type == "public":
            return True
        if key.user_id == user_id:
            return True
        return False

    def _can_modify(self, key: ApiKey, user_id: Optional[int], user_role: str) -> bool:
        """检查用户是否有权修改/删除密钥"""
        if user_role == "admin":
            return True
        if key.key_type == "private" and key.user_id == user_id:
            return True
        return False

    def _to_dict(self, key: ApiKey, include_encrypted: bool = False) -> Dict[str, Any]:
        result = {
            "id": key.id,
            "source_config_id": key.source_config_id,
            "key_type": key.key_type,
            "user_id": key.user_id,
            "key_alias": key.key_alias,
            "key_hint": key.key_hint,
            "status": key.status,
            "weight": key.weight,
            "consecutive_errors": key.consecutive_errors,
            "last_error_at": key.last_error_at.isoformat() if key.last_error_at else None,
            "max_consecutive_errors": key.max_consecutive_errors,
            "daily_call_limit": key.daily_call_limit,
            "current_daily_calls": key.current_daily_calls,
            "last_reset_at": key.last_reset_at.isoformat() if key.last_reset_at else None,
            "total_calls": key.total_calls,
            "created_by": key.created_by,
            "created_at": key.created_at.isoformat() if key.created_at else None,
            "updated_at": key.updated_at.isoformat() if key.updated_at else None,
        }
        if include_encrypted:
            result["encrypted_key_value"] = key.encrypted_key_value
        return result


# Singleton
_api_key_service: Optional[ApiKeyService] = None


def get_api_key_service() -> ApiKeyService:
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = ApiKeyService()
    return _api_key_service
