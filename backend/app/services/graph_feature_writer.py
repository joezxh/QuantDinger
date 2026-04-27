"""Feature writer service for graph ORM persistence."""
from datetime import date
from typing import List, Type

from app.database.repositories.graph_repository import GraphRepository
from app.database.session import get_session
from app.models.graph_domain import CompanyNarrativeFeature, CryptoNarrativeFeature, PolymarketMarketFeature
from app.models.graph_meta import GraphFeatureDaily


class GraphFeatureWriter:
    def _coerce_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def build_daily_features(self, *, market: str, symbol: str, source: str, features: dict) -> List[GraphFeatureDaily]:
        rows: List[GraphFeatureDaily] = []
        for name, value in (features or {}).items():
            numeric_value = self._coerce_float(value)
            if numeric_value is None:
                continue
            rows.append(
                GraphFeatureDaily(
                    trade_date=date.today(),
                    market=market,
                    symbol=symbol,
                    feature_name=name,
                    feature_value=numeric_value,
                    source=source,
                )
            )
        return rows

    def build_domain_features(
        self,
        *,
        model_class: Type,
        id_field: str,
        id_value: str,
        metric_field: str,
        source: str,
        features: dict,
    ):
        rows = []
        for name, value in (features or {}).items():
            numeric_value = self._coerce_float(value)
            if numeric_value is None:
                continue

            payload = {
                "trade_date": date.today(),
                id_field: id_value,
                "source": source,
            }

            if model_class in {CompanyNarrativeFeature, CryptoNarrativeFeature}:
                payload["narrative_name"] = name
                payload[metric_field] = numeric_value
            elif model_class is PolymarketMarketFeature:
                payload["feature_name"] = name
                payload[metric_field] = numeric_value
            else:
                continue

            rows.append(model_class(**payload))
        return rows

    def _write_rows(self, rows, writer_name: str) -> int:
        if not rows:
            return 0
        try:
            with get_session() as session:
                repo = GraphRepository(session)
                getattr(repo, writer_name)(rows)
            return len(rows)
        except Exception:
            return 0

    def write_daily_features(self, *, market: str, symbol: str, source: str, features: dict) -> int:
        rows = self.build_daily_features(market=market, symbol=symbol, source=source, features=features)
        return self._write_rows(rows, "insert_feature_batch")

    def write_company_narrative_features(self, ticker: str, source: str, features: dict) -> int:
        rows = self.build_domain_features(
            model_class=CompanyNarrativeFeature,
            id_field="ticker",
            id_value=ticker,
            metric_field="narrative_score",
            source=source,
            features=features,
        )
        return self._write_rows(rows, "insert_company_narrative_features")

    def write_crypto_narrative_features(self, symbol: str, source: str, features: dict) -> int:
        rows = self.build_domain_features(
            model_class=CryptoNarrativeFeature,
            id_field="symbol",
            id_value=symbol,
            metric_field="narrative_score",
            source=source,
            features=features,
        )
        return self._write_rows(rows, "insert_crypto_narrative_features")

    def write_polymarket_market_features(self, market_id: str, source: str, features: dict) -> int:
        rows = self.build_domain_features(
            model_class=PolymarketMarketFeature,
            id_field="market_id",
            id_value=market_id,
            metric_field="feature_value",
            source=source,
            features=features,
        )
        return self._write_rows(rows, "insert_polymarket_market_features")
