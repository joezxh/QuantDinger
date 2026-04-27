"""Exchange execution helpers (local deployment)."""
from __future__ import annotations

import json
from typing import Any, Dict

from app.database.repositories.live_trading_repository import LiveTradingRepository
from app.database.session import get_session
from app.utils.logger import get_logger
from app.utils.credential_crypto import decrypt_credential_blob

logger = get_logger(__name__)


def _safe_json_loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return default
    s = value.strip()
    if not s:
        return default
    try:
        return json.loads(s)
    except Exception:
        return default


def mask_secret(s: str, keep: int = 4) -> str:
    if not s:
        return ""
    s = str(s)
    if len(s) <= keep * 2:
        return s[: max(1, keep)] + "***"
    return f"{s[:keep]}...{s[-keep:]}"


def safe_exchange_config_for_log(cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(cfg, dict):
        return {}
    out = dict(cfg)
    for k in ["api_key", "secret_key", "passphrase", "apiKey", "secret", "password"]:
        if k in out and out.get(k):
            out[k] = mask_secret(str(out.get(k)))
    return out


def load_strategy_configs(strategy_id: int) -> Dict[str, Any]:
    with get_session() as session:
        row = LiveTradingRepository(session).get_strategy_config(int(strategy_id))
    if not row:
        return {}
    exchange_config = _safe_json_loads(getattr(row, "exchange_config", None), {})
    trading_config = _safe_json_loads(getattr(row, "trading_config", None), {})
    market_type = (getattr(row, "market_type", None) or exchange_config.get("market_type") or "swap").strip()
    leverage = float(getattr(row, "leverage", None) or trading_config.get("leverage") or exchange_config.get("leverage") or 1.0)
    execution_mode = (getattr(row, "execution_mode", None) or "signal").strip().lower()
    market_category = (getattr(row, "market_category", None) or "Crypto").strip()
    user_id = int(getattr(row, "user_id", None) or 1)
    return {
        "strategy_id": int(strategy_id),
        "user_id": user_id,
        "exchange_config": exchange_config if isinstance(exchange_config, dict) else {},
        "trading_config": trading_config if isinstance(trading_config, dict) else {},
        "market_type": market_type,
        "leverage": leverage,
        "execution_mode": execution_mode,
        "market_category": market_category,
    }


def _load_credential_config(credential_id: int, user_id: int = 1) -> Dict[str, Any]:
    with get_session() as session:
        row = LiveTradingRepository(session).get_exchange_credential(int(credential_id), int(user_id))
    raw = getattr(row, "encrypted_config", None) if row else None
    try:
        plain = decrypt_credential_blob(raw)
    except ValueError as e:
        logger.warning(f"decrypt credential_id={credential_id}: {e}")
        return {}
    return _safe_json_loads(plain, {}) or {}


def resolve_exchange_config(exchange_config: Dict[str, Any], user_id: int = 1) -> Dict[str, Any]:
    if not isinstance(exchange_config, dict):
        return {}
    merged: Dict[str, Any] = {}
    credential_id = exchange_config.get("credential_id") or exchange_config.get("credentials_id")
    try:
        if credential_id:
            base = _load_credential_config(int(credential_id), user_id=user_id)
            if isinstance(base, dict):
                merged.update(base)
    except Exception as e:
        logger.warning(f"Failed to load credential_id={credential_id}: {e}")
    for k, v in exchange_config.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        merged[k] = v
    return merged
