"""
Market symbols seed data and lookup functions.

Data is stored in PostgreSQL table `qd_market_symbols` (initialized via migrations/init.sql).
This module provides helper functions to query hot symbols, search, and get symbol names.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from sqlalchemy import text

from app.database.session import get_session
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_hot_symbols(market: str, limit: int = 10) -> List[Dict]:
    """
    Get hot symbols for a market.
    
    Args:
        market: Market name (e.g., 'Crypto', 'USStock', 'Forex')
        limit: Maximum number of results
        
    Returns:
        List of {market, symbol, name} dicts
    """
    market = (market or '').strip()
    if not market:
        return []
    
    try:
        with get_session() as session:
            result = session.execute(
                text("""
                    SELECT market, symbol, name FROM qd_market_symbols
                    WHERE market = :market AND is_active = 1 AND is_hot = 1
                    ORDER BY sort_order DESC
                    LIMIT :limit
                """),
                {"market": market, "limit": max(limit, 0)},
            )
            rows = result.mappings().fetchall() or []
            return [{'market': r['market'], 'symbol': r['symbol'], 'name': r.get('name') or ''} for r in rows]
    except Exception as e:
        logger.debug(f"get_hot_symbols from DB failed: {e}")
        return []


def search_symbols(market: str, keyword: str, limit: int = 20) -> List[Dict]:
    """
    Search symbols by keyword.
    
    Args:
        market: Market name
        keyword: Search keyword (matches symbol or name)
        limit: Maximum number of results
        
    Returns:
        List of {market, symbol, name} dicts
    """
    market = (market or '').strip()
    kw = (keyword or '').strip()
    if not market or not kw:
        return []
    
    # Use ILIKE for case-insensitive search in PostgreSQL
    pattern = f'%{kw}%'
    
    try:
        with get_session() as session:
            result = session.execute(
                text("""
                    SELECT market, symbol, name FROM qd_market_symbols
                    WHERE market = :market AND is_active = 1
                      AND (UPPER(symbol) LIKE UPPER(:pattern) OR UPPER(name) LIKE UPPER(:pattern))
                    ORDER BY sort_order DESC
                    LIMIT :limit
                """),
                {"market": market, "pattern": pattern, "limit": max(limit, 0)},
            )
            rows = result.mappings().fetchall() or []
            return [{'market': r['market'], 'symbol': r['symbol'], 'name': r.get('name') or ''} for r in rows]
    except Exception as e:
        logger.debug(f"search_symbols from DB failed: {e}")
        return []


def _normalize_for_match(market: str, symbol: str) -> str:
    """Normalize symbol for matching."""
    m = (market or '').strip()
    s = (symbol or '').strip().upper()
    if not m or not s:
        return s

    return s


def get_symbol_name(market: str, symbol: str) -> Optional[str]:
    """
    Get display name for a symbol.
    
    Args:
        market: Market name
        symbol: Symbol (e.g., 'AAPL', 'BTC/USDT', '600519')
        
    Returns:
        Symbol name or None if not found
    """
    m = (market or '').strip()
    if not m:
        return None

    s = _normalize_for_match(m, symbol)
    if not s:
        return None

    # Crypto: allow user to pass BTC (try BTC/USDT) or full pair
    candidate_symbols = [s]
    if m == 'Crypto' and '/' not in s:
        candidate_symbols.append(f"{s}/USDT")

    try:
        with get_session() as session:
            for cand in candidate_symbols:
                result = session.execute(
                    text("SELECT name FROM qd_market_symbols WHERE market = :market AND UPPER(symbol) = :symbol"),
                    {"market": m, "symbol": cand.upper()},
                )
                row = result.mappings().fetchone()
                if row and row.get('name'):
                    return str(row['name'])
    except Exception as e:
        logger.debug(f"get_symbol_name from DB failed: {e}")

    return None


def get_all_symbols(market: str = None) -> List[Dict]:
    """
    Get all active symbols, optionally filtered by market.
    
    Args:
        market: Optional market filter
        
    Returns:
        List of symbol records
    """
    try:
        with get_session() as session:
            if market:
                result = session.execute(
                    text("""
                        SELECT market, symbol, name, exchange, currency, is_hot, sort_order
                        FROM qd_market_symbols
                        WHERE market = :market AND is_active = 1
                        ORDER BY sort_order DESC
                    """),
                    {"market": market.strip()},
                )
            else:
                result = session.execute(
                    text("""
                        SELECT market, symbol, name, exchange, currency, is_hot, sort_order
                        FROM qd_market_symbols
                        WHERE is_active = 1
                        ORDER BY market, sort_order DESC
                    """),
                )
            rows = result.mappings().fetchall() or []
            return [dict(r) for r in rows]
    except Exception as e:
        logger.debug(f"get_all_symbols from DB failed: {e}")
        return []
