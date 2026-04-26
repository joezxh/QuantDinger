"""USDT Payment Service (方案B：每单独立地址 + 自动对账)

MVP: USDT-TRC20（TronGrid），watch-only xpub 派生地址。
"""
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional, Tuple

from app.database.repositories.runtime_ops_repository import RuntimeOpsRepository
from app.database.session import get_session
from app.utils.logger import get_logger
from app.services.billing_service import get_billing_service

logger = get_logger(__name__)


class UsdtPaymentService:
    _schema_ensured: bool = False

    def __init__(self):
        self.billing = get_billing_service()

    def _get_cfg(self) -> Dict[str, Any]:
        return {
            "enabled": str(os.getenv("USDT_PAY_ENABLED", "False")).lower() in ("1", "true", "yes"),
            "chain": (os.getenv("USDT_PAY_CHAIN", "TRC20") or "TRC20").upper(),
            "xpub_trc20": (os.getenv("USDT_TRC20_XPUB", "") or "").strip(),
            "confirm_seconds": int(float(os.getenv("USDT_PAY_CONFIRM_SECONDS", "30") or 30)),
            "order_expire_minutes": int(float(os.getenv("USDT_PAY_EXPIRE_MINUTES", "30") or 30)),
        }

    def _derive_trc20_address_from_xpub(self, xpub: str, index: int) -> str:
        try:
            from bip_utils import Bip44, Bip44Coins, Bip44Changes
        except Exception as e:
            raise RuntimeError(f"bip_utils_missing:{e}")
        if not xpub:
            raise RuntimeError("missing_xpub")
        if index < 0:
            raise RuntimeError("invalid_index")
        ctx = Bip44.FromExtendedKey(xpub, Bip44Coins.TRON)
        lvl = int(ctx.Level())
        if lvl == 3:
            ctx = ctx.Change(Bip44Changes.CHAIN_EXT)
        elif lvl == 4:
            pass
        elif lvl == 5:
            if index != 0:
                raise RuntimeError("xpub_is_address_level")
            return ctx.PublicKey().ToAddress()
        else:
            raise RuntimeError(f"unsupported_xpub_level:{lvl}")
        return ctx.AddressIndex(index).PublicKey().ToAddress()

    def create_order(self, user_id: int, plan: str) -> Tuple[bool, str, Dict[str, Any]]:
        cfg = self._get_cfg()
        if not cfg["enabled"]:
            return False, "usdt_pay_disabled", {}
        if cfg["chain"] != "TRC20":
            return False, "unsupported_chain", {}
        plan = (plan or "").strip().lower()
        if plan not in ("monthly", "yearly", "lifetime"):
            return False, "invalid_plan", {}
        plans = self.billing.get_membership_plans()
        amount = Decimal(str(plans.get(plan, {}).get("price_usd") or 0))
        if amount <= 0:
            return False, "invalid_amount", {}
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=cfg["order_expire_minutes"])
        try:
            with get_session() as session:
                repo = RuntimeOpsRepository(session)
                max_idx = repo.get_max_usdt_address_index("TRC20")
                next_idx = int(max_idx if max_idx is not None else -1) + 1
                address = self._derive_trc20_address_from_xpub(cfg["xpub_trc20"], next_idx)
                row = repo.create_usdt_order(
                    user_id=user_id,
                    plan=plan,
                    chain="TRC20",
                    amount_usdt=amount,
                    address_index=next_idx,
                    address=address,
                    status="pending",
                    expires_at=expires_at,
                )
            return True, "success", {
                "order_id": row.id,
                "plan": plan,
                "chain": "TRC20",
                "amount_usdt": str(amount),
                "address": address,
                "expires_at": expires_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"create_order failed: {e}", exc_info=True)
            return False, f"error:{str(e)}", {}

    def get_order(self, user_id: int, order_id: int, refresh: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            with get_session() as session:
                row = RuntimeOpsRepository(session).get_usdt_order(order_id, user_id)
            if not row:
                return False, "order_not_found", {}
            return True, "success", {
                "order_id": row.id,
                "plan": row.plan,
                "chain": row.chain,
                "amount_usdt": str(row.amount_usdt or 0),
                "address": row.address or "",
                "status": row.status or "",
                "tx_hash": row.tx_hash or "",
                "paid_at": row.paid_at.isoformat() if row.paid_at else None,
                "confirmed_at": row.confirmed_at.isoformat() if row.confirmed_at else None,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        except Exception as e:
            logger.error(f"get_order failed: {e}", exc_info=True)
            return False, f"error:{str(e)}", {}


_usdt_payment_service_instance: UsdtPaymentService | None = None


def get_usdt_payment_service() -> UsdtPaymentService:
    global _usdt_payment_service_instance
    if _usdt_payment_service_instance is None:
        _usdt_payment_service_instance = UsdtPaymentService()
    return _usdt_payment_service_instance
