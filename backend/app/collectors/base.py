"""Collected item and collector base classes."""
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger


@dataclass
class CollectedItem:
    source: str
    data_type: str
    market: Optional[str]
    symbol: Optional[str]
    raw_data: Dict[str, Any]
    normalized_data: Dict[str, Any]
    collected_at: datetime = field(default_factory=datetime.utcnow)
    content_hash: str = ""
    importance_score: float = 0.5
    should_build_episode: bool = False
    entity_keys: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.content_hash:
            payload = json.dumps(self.normalized_data, sort_keys=True, default=str)
            self.content_hash = hashlib.sha256(payload.encode()).hexdigest()[:32]


class BaseCollector(ABC):
    name: str = "base"

    @abstractmethod
    def collect(self, **kwargs) -> List[CollectedItem]:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError

    def _safe_collect(self, **kwargs) -> List[CollectedItem]:
        try:
            return self.collect(**kwargs)
        except Exception as e:
            get_logger(self.name).error(f"Collect failed: {e}", exc_info=True)
            return []
