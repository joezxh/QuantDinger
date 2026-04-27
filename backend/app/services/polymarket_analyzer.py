"""
Polymarket预测市场分析器
分析预测市场，生成AI预测和交易机会推荐
"""
import json
import re
from typing import Dict, List, Any, Optional

from app.data_sources.polymarket import PolymarketDataSource
from app.database.repositories.polymarket_repository import PolymarketRepository
from app.database.session import get_session
from app.services.llm import LLMService
from app.services.market_data_collector import get_market_data_collector
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PolymarketAnalyzer:
    """预测市场AI分析器"""

    def __init__(self):
        self.llm_service = LLMService()
        self.data_collector = get_market_data_collector()
        self.polymarket_source = PolymarketDataSource()

    def _cache_market_snapshot(self, market: Dict[str, Any]) -> None:
        try:
            with get_session() as session:
                PolymarketRepository(session).upsert_market_snapshot(
                    market_id=str(market.get('id') or market.get('market_id') or ''),
                    question=str(market.get('question') or ''),
                    current_probability=market.get('current_probability'),
                    end_date_iso=market.get('end_date_iso'),
                    payload_json=json.dumps(market, ensure_ascii=False),
                )
        except Exception as e:
            logger.debug(f"Failed to cache polymarket snapshot: {e}")

    def _get_cached_market_snapshot(self, market_id: str) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as session:
                market = PolymarketRepository(session).get_market_by_market_id(market_id)
            if not market:
                return None
            if market.payload_json:
                return json.loads(market.payload_json)
            return {
                'id': market.market_id,
                'market_id': market.market_id,
                'question': market.question,
                'current_probability': float(market.current_probability or 0),
                'end_date_iso': market.end_date_iso,
            }
        except Exception as e:
            logger.debug(f"Failed to read cached polymarket snapshot: {e}")
            return None

    def _serialize_analysis(self, analysis_row) -> Optional[Dict[str, Any]]:
        if not analysis_row:
            return None
        try:
            payload = json.loads(analysis_row.payload_json or '{}')
        except Exception:
            payload = {}
        return {
            'market_id': analysis_row.market_id,
            'ai_predicted_probability': float(analysis_row.ai_predicted_probability or 0),
            'market_probability': float(analysis_row.market_probability or 0),
            'divergence': float(analysis_row.divergence or 0),
            'recommendation': analysis_row.recommendation,
            'confidence_score': float(analysis_row.confidence_score or 0),
            'reasoning': analysis_row.reasoning or '',
            'key_factors': payload.get('key_factors', []),
            'risk_factors': payload.get('risk_factors', []),
            'related_assets': payload.get('related_assets', []),
            'risk_level': analysis_row.risk_level,
            'opportunity_score': float(analysis_row.opportunity_score or 0),
        }

    def _get_cached_analysis(self, market_id: str, user_id: int = None) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as session:
                row = PolymarketRepository(session).get_latest_analysis(market_id, user_id=user_id)
            return self._serialize_analysis(row)
        except Exception as e:
            logger.debug(f"Failed to read cached analysis: {e}")
            return None

    def _is_analysis_fresh(self, analysis: Dict[str, Any], max_age_minutes: int = 30) -> bool:
        return bool(analysis)

    def _save_analysis_to_db(self, analysis: Dict, user_id: int = None, language: str = 'en-US', model: str = None):
        try:
            with get_session() as session:
                PolymarketRepository(session).create_analysis(
                    market_id=str(analysis.get('market_id') or ''),
                    user_id=user_id,
                    ai_predicted_probability=analysis.get('ai_predicted_probability'),
                    market_probability=analysis.get('market_probability'),
                    divergence=analysis.get('divergence'),
                    recommendation=analysis.get('recommendation'),
                    confidence_score=analysis.get('confidence_score'),
                    risk_level=analysis.get('risk_level'),
                    opportunity_score=analysis.get('opportunity_score'),
                    reasoning=analysis.get('reasoning'),
                    payload_json=json.dumps({
                        'key_factors': analysis.get('key_factors', []),
                        'risk_factors': analysis.get('risk_factors', []),
                        'related_assets': analysis.get('related_assets', []),
                        'language': language,
                        'model': model,
                    }, ensure_ascii=False),
                )
        except Exception as e:
            logger.warning(f"Failed to save analysis: {e}")

    def _save_opportunities_to_db(self, market_id: str, opportunities: List[Dict]):
        try:
            rows = []
            for item in opportunities:
                rows.append({
                    'market_id': market_id,
                    'asset': str(item.get('asset') or ''),
                    'market': item.get('market'),
                    'signal': item.get('signal'),
                    'confidence': item.get('confidence'),
                    'reasoning': item.get('reasoning'),
                    'payload_json': json.dumps(item, ensure_ascii=False),
                })
            with get_session() as session:
                PolymarketRepository(session).replace_opportunities(market_id, rows)
        except Exception as e:
            logger.warning(f"Failed to save opportunities: {e}")

    def analyze_market(self, market_id: str, user_id: int = None, use_cache: bool = True, language: str = 'zh-CN', model: str = None) -> Dict:
        try:
            market = self._get_cached_market_snapshot(market_id) if use_cache else None
            if not market:
                market = self.polymarket_source.get_market_details(market_id)
                if not market:
                    return {"error": "Market not found", "market_id": market_id}
                self._cache_market_snapshot(market)

            if use_cache:
                cached_analysis = self._get_cached_analysis(market_id, user_id)
                if cached_analysis and self._is_analysis_fresh(cached_analysis, max_age_minutes=30):
                    logger.debug(f"Using cached analysis for market {market_id}")
                    return cached_analysis

            related_news = self._get_related_news(market['question'])
            related_assets = self._identify_related_assets(market['question'])
            asset_data = self._get_asset_data(related_assets)
            ai_result = self._ai_predict_probability(
                question=market['question'],
                current_market_prob=market['current_probability'],
                related_news=related_news,
                asset_data=asset_data,
                language=language,
            )
            analysis_result = {
                "market_id": market_id,
                "ai_predicted_probability": ai_result['predicted_probability'],
                "market_probability": market['current_probability'],
                "divergence": ai_result['predicted_probability'] - market['current_probability'],
                "recommendation": self._generate_recommendation(
                    divergence=ai_result['predicted_probability'] - market['current_probability'],
                    confidence=ai_result['confidence'],
                ),
                "confidence_score": ai_result['confidence'],
                "reasoning": ai_result['reasoning'],
                "key_factors": ai_result.get('key_factors', []),
                "risk_factors": ai_result.get('risk_factors', []),
                "related_assets": related_assets,
                "risk_level": self._assess_risk(market, ai_result),
                "opportunity_score": self._calculate_opportunity_score(
                    ai_prob=ai_result['predicted_probability'],
                    market_prob=market['current_probability'],
                    confidence=ai_result['confidence'],
                ),
            }
            self._save_analysis_to_db(analysis_result, user_id, language=language, model=model)
            return analysis_result
        except Exception as e:
            logger.error(f"Failed to analyze market {market_id}: {e}", exc_info=True)
            return {"error": str(e), "market_id": market_id}

    def generate_asset_trading_opportunities(self, market_id: str) -> List[Dict]:
        try:
            market_analysis = self.analyze_market(market_id)
            if market_analysis.get('error'):
                return []
            related_assets = market_analysis.get('related_assets', [])
            if not related_assets:
                return []
            opportunities = []
            for asset in related_assets:
                try:
                    market_type = self._infer_market(asset)
                    asset_data = self.data_collector.collect_all(
                        market=market_type,
                        symbol=asset,
                        timeframe="1D",
                        include_polymarket=False,
                    )
                    technical_analysis = self._analyze_technical(asset_data)
                    if market_analysis['recommendation'] == "YES":
                        signal = "BUY" if technical_analysis.get('trend') == "bullish" else "HOLD"
                    elif market_analysis['recommendation'] == "NO":
                        signal = "SELL" if technical_analysis.get('trend') == "bearish" else "HOLD"
                    else:
                        signal = "HOLD"
                    confidence = market_analysis['confidence_score'] * 0.6 + technical_analysis.get('confidence', 50) * 0.4
                    if signal != "HOLD" and confidence > 60:
                        opportunities.append({
                            "asset": asset,
                            "market": market_type,
                            "signal": signal,
                            "confidence": round(confidence, 2),
                            "reasoning": f"预测市场分析：{market_analysis['reasoning'][:200]}。技术面：{technical_analysis.get('summary', '')[:200]}",
                            "related_prediction": {
                                "market_id": market_id,
                                "question": market_analysis.get('question', ''),
                                "ai_probability": market_analysis['ai_predicted_probability'],
                                "market_probability": market_analysis['market_probability'],
                            },
                            "entry_suggestion": technical_analysis.get('entry_suggestion', {}),
                        })
                except Exception as e:
                    logger.debug(f"Failed to analyze asset {asset} for market {market_id}: {e}")
                    continue
            if opportunities:
                self._save_opportunities_to_db(market_id, opportunities)
            return opportunities
        except Exception as e:
            logger.error(f"Failed to generate asset opportunities for {market_id}: {e}")
            return []
