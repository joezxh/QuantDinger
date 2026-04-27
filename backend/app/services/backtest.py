"""
Backtest Service
"""
import hashlib
import json
import os
import threading
import time as _time
import traceback
from datetime import datetime, date
from typing import Dict, List, Any, Optional

import numpy as np
import pandas as pd

from app.data_sources import DataSourceFactory
from app.database.repositories.backtest_repository import BacktestRepository
from app.database.session import get_session
from app.services.indicator_params import IndicatorParamsParser, IndicatorCaller
from app.services.kline import KlineService
from app.utils.logger import get_logger
from app.utils.safe_exec import build_safe_builtins, safe_exec_with_validation

logger = get_logger(__name__)


class _KlineCache:
    """Simple in-memory K-line cache with TTL to avoid repeated external API calls."""

    def __init__(self, max_size: int = 64):
        self._store: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._max_size = max_size

    @staticmethod
    def _ttl_for_timeframe(timeframe: str) -> int:
        if timeframe in ('1m', '5m', '15m', '30m'):
            return 300
        return 1800

    def get(self, key: str) -> Optional[pd.DataFrame]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if _time.time() > entry['expires']:
                del self._store[key]
                return None
            return entry['df'].copy()

    def put(self, key: str, df: pd.DataFrame, timeframe: str):
        ttl = self._ttl_for_timeframe(timeframe)
        with self._lock:
            if len(self._store) >= self._max_size:
                oldest_key = min(self._store, key=lambda k: self._store[k]['expires'])
                del self._store[oldest_key]
            self._store[key] = {
                'df': df.copy(),
                'expires': _time.time() + ttl,
            }


_kline_cache = _KlineCache()


class BacktestService:
    """Backtest Service"""

    TIMEFRAME_SECONDS = {
        '1m': 60, '5m': 300, '15m': 900, '30m': 1800,
        '1H': 3600, '4H': 14400, '1D': 86400, '1W': 604800,
    }

    ENGINE_VERSION = 'strategy-backtest-v1'

    def __init__(self):
        self._storage_schema_ready = False

    def ensure_storage_schema(self) -> None:
        """Schema is managed by Alembic migrations; no runtime ALTER needed."""
        self._storage_schema_ready = True

    def _detect_trade_side(self, trade_type: str) -> str:
        ty = str(trade_type or '').strip().lower()
        if 'long' in ty:
            return 'long'
        if 'short' in ty:
            return 'short'
        return ''

    def get_execution_timeframe(
        self,
        start_date: datetime,
        end_date: datetime,
        market: str,
    ) -> tuple[str, Dict[str, Any]]:
        """Choose the best execution timeframe for a backtest range."""
        delta_days = (end_date - start_date).days
        if delta_days <= 7:
            tf = '1m'
            label = '1 minute'
        elif delta_days <= 30:
            tf = '5m'
            label = '5 minutes'
        elif delta_days <= 90:
            tf = '15m'
            label = '15 minutes'
        elif delta_days <= 365:
            tf = '1H'
            label = '1 hour'
        else:
            tf = '1D'
            label = '1 day'
        return tf, {
            'timeframe': tf,
            'label': label,
            'bars_estimate': max(100, delta_days * 24 * 60 // self.TIMEFRAME_SECONDS.get(tf, 86400)),
        }

    def run(
        self,
        *,
        user_id: int,
        indicator_code: str,
        indicator_id: Optional[int] = None,
        symbol: str,
        market: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0,
        leverage: int = 1,
        trade_direction: str = 'long',
        strategy_config: Optional[Dict[str, Any]] = None,
        enable_mtf: bool = True,
        persist: bool = True,
        use_graph_features: bool = False,
    ) -> Dict[str, Any]:
        """Run a full backtest for an indicator strategy.

        When ``use_graph_features`` is True, graph-derived features are fetched
        from ``qd_graph_feature_daily`` and merged into the K-line DataFrame
        before indicator execution.
        """
        try:
            klines = self._fetch_klines(market, symbol, timeframe, start_date, end_date)
            if not klines:
                return self._error_result("No historical data available for the selected range")

            df = self._klines_to_df(klines)
            if df.empty:
                return self._error_result("Failed to build DataFrame from klines")

            # Optional graph feature injection
            if use_graph_features:
                try:
                    from app.services.graph_feature_injector import GraphFeatureInjector
                    injector = GraphFeatureInjector()
                    df = injector.inject(
                        df,
                        market=market,
                        symbol=symbol,
                        start_date=start_date.date(),
                        end_date=end_date.date(),
                    )
                except Exception as exc:
                    logger.warning(f"Graph feature injection skipped: {exc}")

            # Execute indicator code
            executed_df = self._execute_indicator(
                indicator_code,
                df,
                strategy_config or {},
                market=market,
                symbol=symbol,
                timeframe=timeframe,
                trade_direction=trade_direction,
                leverage=leverage,
                user_id=user_id,
                indicator_id=indicator_id,
            )
            if executed_df is None or executed_df.empty:
                return self._error_result("Indicator execution failed or produced empty output")

            # Simulate trades
            result = self._simulate_trades(
                executed_df,
                initial_capital=initial_capital,
                commission=commission,
                slippage=slippage,
                leverage=leverage,
                trade_direction=trade_direction,
            )

            if persist:
                run_id = self.persist_run(
                    user_id=user_id,
                    indicator_id=indicator_id,
                    strategy_id=None,
                    strategy_name='',
                    run_type='indicator',
                    market=market,
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date_str=start_date.strftime('%Y-%m-%d'),
                    end_date_str=end_date.strftime('%Y-%m-%d'),
                    initial_capital=initial_capital,
                    commission=commission,
                    slippage=slippage,
                    leverage=leverage,
                    trade_direction=trade_direction,
                    strategy_config=strategy_config,
                    status='success',
                    result=result,
                    code=indicator_code,
                )
                result['runId'] = run_id

            return result
        except Exception as exc:
            logger.error(f"Backtest run failed: {exc}")
            logger.error(traceback.format_exc())
            return self._error_result(str(exc))

    def run_strategy_snapshot(
        self,
        snapshot: Dict[str, Any],
        *,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Run backtest from a strategy snapshot (used by experiment runner)."""
        return self.run(
            user_id=int(snapshot.get('user_id', 1)),
            indicator_code=snapshot.get('code') or snapshot.get('indicator_code', ''),
            indicator_id=snapshot.get('indicator_id'),
            symbol=snapshot.get('symbol', ''),
            market=snapshot.get('market', 'crypto'),
            timeframe=snapshot.get('timeframe', '1D'),
            start_date=start_date,
            end_date=end_date,
            initial_capital=float(snapshot.get('initial_capital', 10000)),
            commission=float(snapshot.get('commission', 0.001)),
            slippage=float(snapshot.get('slippage', 0.0)),
            leverage=int(snapshot.get('leverage', 1)),
            trade_direction=str(snapshot.get('trade_direction', 'long')),
            strategy_config=snapshot.get('strategy_config') or {},
            persist=False,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _error_result(self, msg: str) -> Dict[str, Any]:
        return {
            'totalReturn': 0.0,
            'annualReturn': 0.0,
            'maxDrawdown': 0.0,
            'winRate': 0.0,
            'totalTrades': 0,
            'trades': [],
            'equityCurve': [],
            'error': msg,
        }

    def _fetch_klines(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """Fetch historical klines from data sources."""
        cache_key = f"{market}:{symbol}:{timeframe}:{start_date.date()}:{end_date.date()}"
        cached = _kline_cache.get(cache_key)
        if cached is not None:
            return cached.to_dict('records') if hasattr(cached, 'to_dict') else []

        kline_service = KlineService()
        # Estimate limit based on date range
        delta_days = (end_date - start_date).days + 1
        seconds_per_bar = self.TIMEFRAME_SECONDS.get(timeframe, 86400)
        limit = max(100, int(delta_days * 86400 / seconds_per_bar) + 100)
        limit = min(limit, 5000)

        klines = kline_service.get_kline(
            market=market,
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            before_time=int(end_date.timestamp()),
        )
        if klines:
            # Filter by start_date
            start_ts = int(start_date.timestamp())
            klines = [k for k in klines if k.get('time', 0) >= start_ts or k.get('timestamp', 0) >= start_ts]
            df = pd.DataFrame(klines)
            _kline_cache.put(cache_key, df, timeframe)
        return klines

    @staticmethod
    def _klines_to_df(klines: List[Dict[str, Any]]) -> pd.DataFrame:
        df = pd.DataFrame(klines)
        if df.empty:
            return df
        # Normalize column names
        col_map = {
            'timestamp': 'time',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        return df

    def _execute_indicator(
        self,
        indicator_code: str,
        df: pd.DataFrame,
        strategy_config: Dict[str, Any],
        **context,
    ) -> Optional[pd.DataFrame]:
        """Execute indicator code in sandbox and return the mutated DataFrame."""
        if not indicator_code:
            return None

        df = df.copy()
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].astype('float64')

        # Parse params
        declared = IndicatorParamsParser.parse_params(indicator_code)
        user_params = strategy_config.get('indicator_params', {})
        merged_params = IndicatorParamsParser.merge_params(declared, user_params)

        # Build execution env (similar to trading_executor._execute_indicator_df)
        exec_env = {
            'df': df,
            'pd': pd,
            'np': np,
            'params': merged_params,
            'output': None,
            'trading_config': strategy_config,
            'config': strategy_config,
            'leverage': float(context.get('leverage', 1)),
            'initial_capital': float(context.get('initial_capital', 10000)),
            'trade_direction': str(context.get('trade_direction', 'long')),
        }
        exec_env['__builtins__'] = build_safe_builtins()

        # Compatibility fix for pandas 2.0+
        import re
        code = indicator_code
        code = re.sub(r"\.fillna\(\s*method\s*=\s*['\"]ffill['\"]\s*\)", ".ffill()", code)
        code = re.sub(r"\.fillna\(\s*method\s*=\s*['\"]bfill['\"]\s*\)", ".bfill()", code)

        result = safe_exec_with_validation(
            code=code,
            exec_globals=exec_env,
            timeout=60,
        )
        if not result['success']:
            logger.error(f"Indicator execution failed: {result['error']}")
            return None

        executed_df = exec_env.get('df', df)
        # Ensure buy/sell columns exist
        if 'buy' not in executed_df.columns:
            executed_df['buy'] = False
        if 'sell' not in executed_df.columns:
            executed_df['sell'] = False
        executed_df['buy'] = executed_df['buy'].fillna(False).astype(bool)
        executed_df['sell'] = executed_df['sell'].fillna(False).astype(bool)
        return executed_df

    def _simulate_trades(
        self,
        df: pd.DataFrame,
        *,
        initial_capital: float,
        commission: float,
        slippage: float,
        leverage: int,
        trade_direction: str,
    ) -> Dict[str, Any]:
        """Simplified trade simulation from buy/sell signals."""
        td = str(trade_direction or 'long').lower()
        allow_long = td in ('long', 'both')
        allow_short = td in ('short', 'both')

        capital = float(initial_capital)
        position = 0  # 0 = flat, 1 = long, -1 = short
        entry_price = 0.0
        trades: List[Dict[str, Any]] = []
        equity_curve: List[Dict[str, Any]] = []
        wins = 0
        total_trades = 0

        for i in range(len(df)):
            row = df.iloc[i]
            price = float(row['close'])
            timestamp = int(row['time']) if 'time' in row else i

            buy_signal = bool(row.get('buy', False)) and allow_long
            sell_signal = bool(row.get('sell', False)) and (allow_short or position != 0)

            if position == 0:
                if buy_signal:
                    position = 1
                    entry_price = price * (1 + slippage)
                    total_trades += 1
                elif sell_signal and allow_short:
                    position = -1
                    entry_price = price * (1 - slippage)
                    total_trades += 1
            elif position == 1:
                if sell_signal:
                    exit_price = price * (1 - slippage)
                    profit = (exit_price - entry_price) / entry_price * leverage
                    gross_pnl = profit * capital
                    fee = abs(gross_pnl) * commission if commission else 0
                    net_pnl = gross_pnl - fee
                    capital += net_pnl
                    trades.append({
                        'type': 'close_long',
                        'time': timestamp,
                        'price': round(exit_price, 6),
                        'amount': 1.0,
                        'profit': round(net_pnl, 4),
                        'balance': round(capital, 2),
                        'reason': 'Signal',
                    })
                    if net_pnl > 0:
                        wins += 1
                    position = 0
                    if sell_signal and allow_short:
                        position = -1
                        entry_price = price * (1 - slippage)
                        total_trades += 1
            elif position == -1:
                if buy_signal:
                    exit_price = price * (1 + slippage)
                    profit = (entry_price - exit_price) / entry_price * leverage
                    gross_pnl = profit * capital
                    fee = abs(gross_pnl) * commission if commission else 0
                    net_pnl = gross_pnl - fee
                    capital += net_pnl
                    trades.append({
                        'type': 'close_short',
                        'time': timestamp,
                        'price': round(exit_price, 6),
                        'amount': 1.0,
                        'profit': round(net_pnl, 4),
                        'balance': round(capital, 2),
                        'reason': 'Signal',
                    })
                    if net_pnl > 0:
                        wins += 1
                    position = 0
                    if buy_signal and allow_long:
                        position = 1
                        entry_price = price * (1 + slippage)
                        total_trades += 1

            equity_curve.append({
                'time': timestamp,
                'value': round(capital, 2),
            })

        total_return = (capital - initial_capital) / initial_capital * 100 if initial_capital else 0
        win_rate = (wins / total_trades * 100) if total_trades else 0

        # Max drawdown
        peak = initial_capital
        max_dd = 0.0
        for pt in equity_curve:
            val = pt['value']
            if val > peak:
                peak = val
            dd = (peak - val) / peak * 100 if peak else 0
            if dd > max_dd:
                max_dd = dd

        return {
            'totalReturn': round(total_return, 4),
            'annualReturn': round(total_return, 4),  # Simplified
            'maxDrawdown': round(max_dd, 4),
            'winRate': round(win_rate, 4),
            'totalTrades': total_trades,
            'trades': trades,
            'equityCurve': equity_curve,
        }

    def persist_run(
        self,
        *,
        user_id: int,
        market: str,
        symbol: str,
        timeframe: str,
        start_date_str: str,
        end_date_str: str,
        initial_capital: float,
        commission: float,
        slippage: float,
        leverage: int,
        trade_direction: str,
        strategy_config: Optional[Dict[str, Any]] = None,
        config_snapshot: Optional[Dict[str, Any]] = None,
        status: str = 'success',
        error_message: str = '',
        result: Optional[Dict[str, Any]] = None,
        indicator_id: Optional[int] = None,
        strategy_id: Optional[int] = None,
        strategy_name: str = '',
        run_type: str = 'indicator',
        code: str = '',
    ) -> Optional[int]:
        self.ensure_storage_schema()
        try:
            with get_session() as session:
                repo = BacktestRepository(session)
                run = repo.create_run(
                    user_id=int(user_id or 1),
                    strategy_id=int(strategy_id) if strategy_id is not None else None,
                    run_type=str(run_type or 'indicator'),
                    strategy_name=str(strategy_name or ''),
                    engine_version=self.ENGINE_VERSION,
                    code_hash=hashlib.sha256(str(code or '').encode('utf-8')).hexdigest() if code else '',
                    config_snapshot=json.dumps(config_snapshot or {}, ensure_ascii=False),
                    total_return=((result or {}).get('totalReturn') if isinstance(result, dict) else None),
                    win_rate=((result or {}).get('winRate') if isinstance(result, dict) else None),
                    max_drawdown=((result or {}).get('maxDrawdown') if isinstance(result, dict) else None),
                    payload_json=json.dumps({
                        'indicator_id': indicator_id,
                        'market': market,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'start_date': start_date_str,
                        'end_date': end_date_str,
                        'initial_capital': initial_capital,
                        'commission': commission,
                        'slippage': slippage,
                        'leverage': leverage,
                        'trade_direction': trade_direction,
                        'strategy_config': strategy_config or {},
                        'status': status,
                        'error_message': error_message,
                        'result': result or {},
                    }, ensure_ascii=False),
                )

                if status == 'success' and isinstance(result, dict):
                    for idx, trade in enumerate((result.get('trades') or []), start=1):
                        repo.add_trade(
                            run_id=run.id,
                            user_id=int(user_id or 1),
                            strategy_id=int(strategy_id) if strategy_id is not None else None,
                            trade_index=idx,
                            trade_time=str(trade.get('time') or ''),
                            trade_type=str(trade.get('type') or ''),
                            side=self._detect_trade_side(trade.get('type')),
                            price=float(trade.get('price') or 0),
                            amount=float(trade.get('amount') or 0),
                            profit=float(trade.get('profit') or 0),
                            balance=float(trade.get('balance') or 0),
                            reason=str(trade.get('reason') or trade.get('close_reason') or ''),
                            payload_json=json.dumps(trade or {}, ensure_ascii=False),
                        )

                    for idx, point in enumerate((result.get('equityCurve') or []), start=1):
                        repo.add_equity_point(
                            run_id=run.id,
                            point_index=idx,
                            point_time=str(point.get('time') or ''),
                            point_value=float(point.get('value') or 0),
                        )

                return run.id
        except Exception:
            logger.warning("Failed to persist backtest run", exc_info=True)
            return None

    def list_runs(self, *, user_id: int, limit: int = 50, offset: int = 0, **kwargs) -> List[Dict[str, Any]]:
        self.ensure_storage_schema()
        try:
            with get_session() as session:
                runs = BacktestRepository(session).list_user_runs(int(user_id or 1), limit=limit + offset)
            rows = runs[offset:offset + limit]
            return [self._hydrate_run_model(r) for r in rows]
        except Exception:
            logger.warning("Failed to list backtest runs", exc_info=True)
            return []

    def get_run(self, *, user_id: int, run_id: int) -> Optional[Dict[str, Any]]:
        self.ensure_storage_schema()
        try:
            with get_session() as session:
                run = BacktestRepository(session).get_run_by_id(int(run_id))
            if not run or int(getattr(run, 'user_id', 0) or 0) != int(user_id or 1):
                return None
            return self._hydrate_run_model(run, include_result=True)
        except Exception:
            logger.warning("Failed to get backtest run", exc_info=True)
            return None

    def _hydrate_run_model(self, run, include_result: bool = False) -> Dict[str, Any]:
        payload = {}
        try:
            payload = json.loads(getattr(run, 'payload_json', '') or '{}')
        except Exception:
            payload = {}
        result = payload.get('result') or {}
        item = {
            'id': run.id,
            'user_id': run.user_id,
            'indicator_id': payload.get('indicator_id'),
            'strategy_id': run.strategy_id,
            'strategy_name': run.strategy_name,
            'run_type': run.run_type,
            'market': payload.get('market', ''),
            'symbol': payload.get('symbol', ''),
            'timeframe': payload.get('timeframe', ''),
            'start_date': payload.get('start_date', ''),
            'end_date': payload.get('end_date', ''),
            'initial_capital': payload.get('initial_capital', 0),
            'commission': payload.get('commission', 0),
            'slippage': payload.get('slippage', 0),
            'leverage': payload.get('leverage', 1),
            'trade_direction': payload.get('trade_direction', 'long'),
            'strategy_config': payload.get('strategy_config', {}),
            'config_snapshot': json.loads(run.config_snapshot or '{}') if getattr(run, 'config_snapshot', None) else {},
            'engine_version': run.engine_version,
            'code_hash': run.code_hash,
            'status': payload.get('status', 'success'),
            'error_message': payload.get('error_message', ''),
            'created_at': run.created_at,
            'total_return': run.total_return,
            'win_rate': run.win_rate,
            'max_drawdown': run.max_drawdown,
            'total_trades': result.get('totalTrades'),
            'annual_return': result.get('annualReturn'),
        }
        if include_result:
            item['result'] = result
        return item
