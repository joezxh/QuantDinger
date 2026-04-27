"""
Analysis Memory System 2.0
Simplified memory for fast analysis service.
"""
import json
from typing import Dict, Any, List, Optional

from app.database.repositories.runtime_ops_repository import RuntimeOpsRepository
from app.database.session import get_session
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _safe_json_parse(val, default=None):
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return default
    return default


class AnalysisMemory:
    def __init__(self):
        pass

    def store(self, analysis_result: Dict[str, Any], user_id: int = None) -> Optional[int]:
        try:
            consensus = analysis_result.get("consensus") or {}
            with get_session() as session:
                row = RuntimeOpsRepository(session).create_analysis_memory(
                    user_id=user_id,
                    market=analysis_result.get("market"),
                    symbol=analysis_result.get("symbol"),
                    decision=analysis_result.get("decision"),
                    confidence=analysis_result.get("confidence"),
                    price_at_analysis=analysis_result.get("market_data", {}).get("current_price"),
                    summary=analysis_result.get("summary"),
                    reasons=json.dumps(analysis_result.get("reasons", [])),
                    scores=json.dumps(analysis_result.get("scores", {})),
                    indicators_snapshot=json.dumps(analysis_result.get("indicators", {})),
                    raw_result=json.dumps(analysis_result),
                    consensus_score=consensus.get("consensus_score"),
                    consensus_abs=consensus.get("consensus_abs"),
                    agreement_ratio=consensus.get("agreement_ratio"),
                    quality_multiplier=consensus.get("quality_multiplier"),
                    task_status="completed",
                    task_error="",
                )
            logger.info(f"Stored analysis memory #{row.id} for {analysis_result.get('symbol')} by user {user_id}")
            return row.id
        except Exception as e:
            logger.error(f"Failed to store analysis memory: {e}", exc_info=True)
            return None

    def get_recent(self, market: str, symbol: str, days: int = 7, limit: int = 5) -> List[Dict]:
        try:
            with get_session() as session:
                rows = RuntimeOpsRepository(session).list_recent_analysis_memory(market, symbol, days, limit)
            results = []
            for row in rows:
                results.append({
                    "id": row.id,
                    "decision": row.decision,
                    "confidence": row.confidence,
                    "price": float(row.price_at_analysis) if row.price_at_analysis else None,
                    "summary": row.summary,
                    "reasons": _safe_json_parse(row.reasons, []),
                    "scores": _safe_json_parse(row.scores, {}),
                    "status": row.task_status or 'completed',
                    "error_message": row.task_error or '',
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "was_correct": row.was_correct,
                    "actual_return_pct": float(row.actual_return_pct) if row.actual_return_pct else None,
                })
            return results
        except Exception as e:
            logger.error(f"Failed to get recent memories: {e}")
            return []


_analysis_memory_instance: AnalysisMemory | None = None


def get_analysis_memory() -> AnalysisMemory:
    global _analysis_memory_instance
    if _analysis_memory_instance is None:
        _analysis_memory_instance = AnalysisMemory()
    return _analysis_memory_instance
