"""DB helpers for recording live trades and maintaining local position snapshots."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.database.repositories.live_trading_repository import LiveTradingRepository
from app.database.session import get_session


def normalize_strategy_symbol(symbol: str) -> str:
    s = str(symbol or "").strip().upper().replace("-", "")
    if not s:
        return ""
    if "/" in s:
        return s
    for quote in ("USDT", "USDC", "USD", "BUSD", "EUR"):
        if s.endswith(quote) and len(s) > len(quote):
            return f"{s[: -len(quote)]}/{quote}"
    return s


def _position_symbol_candidates(symbol: str) -> List[str]:
    raw = str(symbol or "").strip()
    if not raw:
        return []
    norm = normalize_strategy_symbol(raw)
    compact = norm.replace("/", "")
    raw_compact = raw.upper().replace("/", "").replace("-", "")
    out: List[str] = []
    for x in (raw, raw.upper(), norm, compact, raw_compact):
        if x and x not in out:
            out.append(x)
    return out


def _fetch_position(strategy_id: int, symbol: str, side: str) -> Dict[str, Any]:
    with get_session() as session:
        row = LiveTradingRepository(session).get_position(int(strategy_id), str(symbol), str(side))
    if not row:
        return {}
    return {
        'id': row.id,
        'user_id': row.user_id,
        'strategy_id': row.strategy_id,
        'symbol': row.symbol,
        'side': row.side,
        'size': row.size,
        'entry_price': row.entry_price,
        'current_price': row.current_price,
        'highest_price': row.highest_price,
        'lowest_price': row.lowest_price,
    }


def _fetch_position_fuzzy(strategy_id: int, symbol: str, side: str) -> Tuple[Dict[str, Any], str]:
    side_l = str(side or "").strip().lower()
    for sym in _position_symbol_candidates(symbol):
        row = _fetch_position(strategy_id, sym, side_l)
        if row and float(row.get("size") or 0.0) > 0:
            db_sym = str(row.get("symbol") or sym).strip()
            return row, db_sym or sym
    canon = normalize_strategy_symbol(symbol) or str(symbol or "").strip()
    return {}, canon


def _resolve_write_symbol(current: Dict[str, Any], cur_size: float, input_symbol: str) -> str:
    if cur_size > 0 and current and str(current.get("symbol") or "").strip():
        return str(current.get("symbol") or "").strip()
    return normalize_strategy_symbol(input_symbol) or str(input_symbol or "").strip()


def _get_user_id_from_strategy(strategy_id: int) -> int:
    from app.services.exchange_execution import load_strategy_configs
    try:
        return int((load_strategy_configs(strategy_id) or {}).get('user_id') or 1)
    except Exception:
        return 1


def record_trade(*, strategy_id: int, symbol: str, trade_type: str, price: float, amount: float, commission: float = 0.0, commission_ccy: str = "", profit: Optional[float] = None, user_id: int = None) -> None:
    value = float(amount or 0.0) * float(price or 0.0)
    if user_id is None:
        user_id = _get_user_id_from_strategy(strategy_id)
    sym_out = normalize_strategy_symbol(symbol) or str(symbol or "").strip()
    with get_session() as session:
        LiveTradingRepository(session).add_trade(
            user_id=int(user_id), strategy_id=int(strategy_id), symbol=sym_out, type=str(trade_type),
            price=float(price or 0.0), amount=float(amount or 0.0), value=float(value),
            commission=float(commission or 0.0), commission_ccy=str(commission_ccy or ""), profit=profit or 0.0,
        )


def _delete_position(strategy_id: int, symbol: str, side: str) -> None:
    with get_session() as session:
        LiveTradingRepository(session).delete_position(int(strategy_id), str(symbol), str(side))


def upsert_position(*, strategy_id: int, symbol: str, side: str, size: float, entry_price: float, current_price: float, highest_price: float = 0.0, lowest_price: float = 0.0, user_id: int = None) -> None:
    if user_id is None:
        user_id = _get_user_id_from_strategy(strategy_id)
    with get_session() as session:
        LiveTradingRepository(session).upsert_position(
            user_id=int(user_id), strategy_id=int(strategy_id), symbol=str(symbol), side=str(side),
            size=float(size or 0.0), entry_price=float(entry_price or 0.0), current_price=float(current_price or 0.0),
            highest_price=float(highest_price or 0.0), lowest_price=float(lowest_price or 0.0),
        )


def apply_fill_to_local_position(*, strategy_id: int, symbol: str, signal_type: str, filled: float, avg_price: float) -> Tuple[Optional[float], Optional[Dict[str, Any]]]:
    sig = (signal_type or "").strip().lower()
    filled_qty = float(filled or 0.0)
    px = float(avg_price or 0.0)
    if filled_qty <= 0 or px <= 0:
        return None, None
    if "long" in sig:
        side = "long"
    elif "short" in sig:
        side = "short"
    else:
        return None, None
    is_open = sig.startswith("open_") or sig.startswith("add_")
    is_close = sig.startswith("close_") or sig.startswith("reduce_")
    sid = int(strategy_id)
    current, _matched = _fetch_position_fuzzy(sid, symbol, side)
    cur_size = float(current.get("size") or 0.0)
    cur_entry = float(current.get("entry_price") or 0.0)
    cur_high = float(current.get("highest_price") or 0.0)
    cur_low = float(current.get("lowest_price") or 0.0)
    sym_key = _resolve_write_symbol(current, cur_size, symbol)
    profit: Optional[float] = None
    if is_open:
        new_size = cur_size + filled_qty
        if new_size <= 0:
            return None, None
        new_entry = (cur_size * cur_entry + filled_qty * px) / new_size if cur_size > 0 and cur_entry > 0 else px
        upsert_position(strategy_id=sid, symbol=sym_key, side=side, size=new_size, entry_price=new_entry, current_price=px, highest_price=max(cur_high or px, px), lowest_price=min(cur_low or px, px))
        return None, _fetch_position(sid, sym_key, side)
    if is_close:
        if cur_size > 0 and cur_entry > 0:
            close_qty = min(cur_size, filled_qty)
            profit = (px - cur_entry) * close_qty if side == "long" else (cur_entry - px) * close_qty
        new_size = cur_size - filled_qty
        if new_size <= 0:
            _delete_position(sid, sym_key, side)
            return profit, None
        upsert_position(strategy_id=sid, symbol=sym_key, side=side, size=new_size, entry_price=cur_entry if cur_entry > 0 else px, current_price=px, highest_price=max(cur_high or px, px), lowest_price=min(cur_low or px, px))
        return profit, _fetch_position(sid, sym_key, side)
    return None, None
