"""Graph feature injector — merge graph-derived features into a backtest DataFrame.

This module bridges the knowledge graph (Neo4j / PostgreSQL graph_feature tables)
with the indicator backtest pipeline.  When a backtest is configured to use graph
features, the injector fetches daily graph features for the target symbol and
aligns them to the K-line DataFrame so that indicator scripts can reference
columns like ``df['graph_sentiment']`` or ``df['narrative_momentum']``.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

from app.database.session import get_session
from app.database.repositories.graph_repository import GraphRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GraphFeatureInjector:
    """Inject graph features into a backtest DataFrame.

    Usage::

        injector = GraphFeatureInjector()
        df_with_features = injector.inject(
            df,
            market="USStock",
            symbol="AAPL",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
    """

    # Feature names that are injected by default when available.
    # Indicator code can reference any of these column names on ``df``.
    DEFAULT_FEATURE_NAMES: List[str] = [
        "graph_sentiment",
        "narrative_momentum",
        "entity_activity",
        "relation_strength",
        "event_impact",
    ]

    def __init__(self, feature_names: Optional[List[str]] = None):
        self.feature_names = feature_names or list(self.DEFAULT_FEATURE_NAMES)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def inject(
        self,
        df: pd.DataFrame,
        *,
        market: str,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        feature_names: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Return a new DataFrame with graph features merged on the date index.

        Parameters
        ----------
        df:
            K-line DataFrame.  Must contain a ``time`` column (unix ms) or a
            DatetimeIndex.
        market:
            Market domain (e.g. ``"USStock"``, ``"crypto"``).
        symbol:
            Symbol / ticker.
        start_date, end_date:
            Optional date bounds (inclusive).  If omitted, inferred from ``df``.
        feature_names:
            Override the list of features to inject.  If ``None``, uses
            ``self.feature_names``.

        Returns
        -------
        DataFrame with additional columns for each successfully fetched feature.
        Missing feature values are forward-filled then back-filled so that
        indicator scripts never see NaN.
        """
        if df is None or df.empty:
            return df

        names = feature_names or self.feature_names
        if not names:
            return df.copy()

        try:
            features_df = self._fetch_features(
                market=market,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                feature_names=names,
            )
        except Exception as exc:
            logger.warning(
                f"Failed to fetch graph features for {market}:{symbol}: {exc}"
            )
            return df.copy()

        if features_df is None or features_df.empty:
            logger.info(f"No graph features found for {market}:{symbol}")
            return df.copy()

        return self._merge(df, features_df)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_features(
        self,
        *,
        market: str,
        symbol: str,
        start_date: Optional[date],
        end_date: Optional[date],
        feature_names: List[str],
    ) -> Optional[pd.DataFrame]:
        """Fetch graph features from PG and return a DataFrame indexed by date."""
        with get_session() as session:
            repo = GraphRepository(session)
            rows = repo.get_features_by_symbol(
                market=market,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

        if not rows:
            return None

        # Build a dict of {feature_name: {trade_date: value}}
        data: Dict[str, Dict[date, float]] = {name: {} for name in feature_names}
        for row in rows:
            fname = getattr(row, "feature_name", None)
            if fname not in data:
                continue
            tdate = getattr(row, "trade_date", None)
            if tdate is None:
                continue
            val = getattr(row, "feature_value", None)
            if val is None:
                continue
            data[fname][tdate] = float(val)

        # Convert to DataFrame
        records = []
        all_dates = set()
        for fname, dvals in data.items():
            all_dates.update(dvals.keys())

        for d in sorted(all_dates):
            record: Dict[str, Any] = {"trade_date": d}
            for fname in feature_names:
                record[fname] = data[fname].get(d, np.nan)
            records.append(record)

        if not records:
            return None

        df = pd.DataFrame(records)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df.set_index("trade_date")
        return df

    def _merge(self, df: pd.DataFrame, features_df: pd.DataFrame) -> pd.DataFrame:
        """Merge features into the K-line DataFrame on date."""
        df = df.copy()

        # Ensure df has a datetime index or derive one from 'time'
        if not isinstance(df.index, pd.DatetimeIndex):
            if "time" in df.columns:
                # time may be unix ms or datetime strings
                df["_dt"] = pd.to_datetime(df["time"], unit="ms", errors="coerce")
                if df["_dt"].isna().all():
                    df["_dt"] = pd.to_datetime(df["time"], errors="coerce")
                df = df.set_index("_dt")
            else:
                logger.warning("DataFrame has no datetime index and no 'time' column; cannot merge graph features")
                return df

        # Normalize indices to date-only for merging
        df_dates = df.index.normalize()
        feat_dates = features_df.index.normalize()

        # Align feature values to df rows by date
        for col in features_df.columns:
            aligned = pd.Series(index=df.index, dtype=float)
            for feat_date, row in features_df.iterrows():
                mask = df_dates == feat_date.normalize()
                aligned.loc[mask] = row[col]
            df[col] = aligned

        # Forward-fill then back-fill so indicator scripts never see NaN
        for col in features_df.columns:
            if col in df.columns:
                df[col] = df[col].ffill().bfill()

        return df
