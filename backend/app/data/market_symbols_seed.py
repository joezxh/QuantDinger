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
            from app.database.repositories.market_symbol_repository import MarketSymbolRepository
            repo = MarketSymbolRepository(session)
            symbols = repo.list_hot_by_market(market, limit=max(limit, 0))
            return [{'market': s.market, 'symbol': s.symbol, 'name': s.name or ''} for s in symbols]
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
    try:
        with get_session() as session:
            from app.database.repositories.market_symbol_repository import MarketSymbolRepository
            repo = MarketSymbolRepository(session)
            symbols = repo.search_symbols(market, keyword, limit=max(limit, 0))
            return [{'market': s.market, 'symbol': s.symbol, 'name': s.name or ''} for s in symbols]
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
            from app.database.repositories.market_symbol_repository import MarketSymbolRepository
            repo = MarketSymbolRepository(session)
            for cand in candidate_symbols:
                symbol_obj = repo.get_by_symbol(m, cand)
                if symbol_obj and symbol_obj.name:
                    return str(symbol_obj.name)
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
            from app.database.repositories.market_symbol_repository import MarketSymbolRepository
            repo = MarketSymbolRepository(session)
            symbols = repo.list_all(market=market.strip() if market else None)
            return [
                {
                    'market': s.market,
                    'symbol': s.symbol,
                    'name': s.name,
                    'exchange': s.exchange,
                    'currency': s.currency,
                    'is_hot': s.is_hot,
                    'sort_order': s.sort_order
                }
                for s in symbols
            ]
    except Exception as e:
        logger.debug(f"get_all_symbols from DB failed: {e}")
        return []
