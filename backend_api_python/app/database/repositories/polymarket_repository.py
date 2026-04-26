"""Polymarket repository helpers."""
from sqlalchemy import delete, select

from app.database.repositories.base import BaseRepository
from app.models.polymarket import (
    PolymarketAnalysis,
    PolymarketMarket,
    PolymarketOpportunity,
    PolymarketUser,
)


class PolymarketRepository(BaseRepository):
    def get_market_by_market_id(self, market_id: str):
        stmt = select(PolymarketMarket).where(PolymarketMarket.market_id == market_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_user_by_address(self, address: str):
        stmt = select(PolymarketUser).where(PolymarketUser.address == address)
        return self.session.execute(stmt).scalar_one_or_none()

    def upsert_market_snapshot(self, *, market_id: str, question: str, current_probability=None, end_date_iso=None, payload_json=None):
        market = self.get_market_by_market_id(market_id)
        if market is None:
            market = PolymarketMarket(
                market_id=market_id,
                question=question,
                current_probability=current_probability,
                end_date_iso=end_date_iso,
                payload_json=payload_json,
            )
            self.add(market)
        else:
            market.question = question
            market.current_probability = current_probability
            market.end_date_iso = end_date_iso
            market.payload_json = payload_json
        self.flush()
        return market

    def create_analysis(self, **kwargs):
        analysis = PolymarketAnalysis(**kwargs)
        self.add(analysis)
        self.flush()
        return analysis

    def replace_opportunities(self, market_id: str, opportunities: list[dict]):
        self.session.execute(delete(PolymarketOpportunity).where(PolymarketOpportunity.market_id == market_id))
        created = []
        for item in opportunities:
            row = PolymarketOpportunity(**item)
            self.add(row)
            created.append(row)
        self.flush()
        return created

    def get_latest_analysis(self, market_id: str, user_id=None):
        stmt = select(PolymarketAnalysis).where(PolymarketAnalysis.market_id == market_id)
        if user_id is not None:
            stmt = stmt.where(PolymarketAnalysis.user_id == user_id)
        stmt = stmt.order_by(PolymarketAnalysis.id.desc())
        return self.session.execute(stmt).scalars().first()

    def delete_analysis_by_market(self, market_id: str, user_id=None):
        stmt = delete(PolymarketAnalysis).where(PolymarketAnalysis.market_id == market_id)
        if user_id is not None:
            stmt = stmt.where(PolymarketAnalysis.user_id == user_id)
        self.session.execute(stmt)
        self.flush()

    def save_batch_analysis(self, markets: list[dict]):
        """Save batch analysis: delete old generic analyses then insert new ones."""
        for market in markets:
            market_id = market.get('market_id')
            ai_analysis = market.get('ai_analysis')
            if not market_id or not ai_analysis:
                continue
            try:
                self.delete_analysis_by_market(market_id, user_id=None)
                self.create_analysis(
                    market_id=market_id,
                    user_id=None,
                    ai_predicted_probability=float(ai_analysis.get('predicted_probability', market.get('current_probability', 50.0))),
                    market_probability=float(market.get('current_probability', 50.0)),
                    divergence=float(ai_analysis.get('divergence', 0)),
                    recommendation=ai_analysis.get('recommendation', 'HOLD'),
                    confidence_score=float(ai_analysis.get('confidence_score', 0)),
                    opportunity_score=float(ai_analysis.get('opportunity_score', 0)),
                    reasoning=ai_analysis.get('reasoning', ''),
                    key_factors=ai_analysis.get('key_factors', []),
                    related_assets=[],
                )
            except Exception:
                continue
