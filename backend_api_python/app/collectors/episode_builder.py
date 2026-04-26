"""Episode builder for graph ingestion."""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class EpisodeEnvelope:
    episode_type: str
    market_domain: str
    title: str
    content: str
    entity_keys: Dict[str, str]
    source: str
    source_ref: str
    event_time: Optional[datetime]
    observed_time: datetime
    importance_score: float = 0.5
    dedup_key: str = ""
    metadata: Optional[Dict[str, Any]] = None


class EpisodeBuilder:
    def build(self, item) -> Optional[EpisodeEnvelope]:
        if not getattr(item, "should_build_episode", False):
            return None

        content_hash = getattr(item, "content_hash", "")
        market = (getattr(item, "market", None) or "unknown").lower()
        symbol = getattr(item, "symbol", None) or getattr(item, "source", "item")
        normalized_data = getattr(item, "normalized_data", {}) or {}
        collected_at = getattr(item, "collected_at", datetime.utcnow())

        return EpisodeEnvelope(
            episode_type=getattr(item, "data_type", "unknown"),
            market_domain=market,
            title=f"{getattr(item, 'data_type', 'event')}:{symbol}",
            content=self._build_content(normalized_data),
            entity_keys=getattr(item, "entity_keys", {}) or {},
            source=getattr(item, "source", "unknown"),
            source_ref=content_hash,
            event_time=normalized_data.get("event_time"),
            observed_time=collected_at,
            importance_score=float(getattr(item, "importance_score", 0.5) or 0.5),
            dedup_key=f"episode:{content_hash}" if content_hash else "",
            metadata=normalized_data,
        )

    def _build_content(self, normalized_data: Dict[str, Any]) -> str:
        return json.dumps(normalized_data, ensure_ascii=False, default=str, sort_keys=True)
