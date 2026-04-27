"""Dedup engine for collected items."""
from app.collectors.storage import CollectorStorage


class DedupEngine:
    def __init__(self, collector_storage=None):
        self._cache = set()
        self.collector_storage = collector_storage or CollectorStorage()

    def filter(self, items):
        new_items = []
        for item in items:
            if self._in_memory_seen(item.content_hash):
                continue
            if self._in_repository(item.content_hash):
                continue
            self._cache.add(item.content_hash)
            new_items.append(item)
        return new_items

    def _in_memory_seen(self, content_hash: str) -> bool:
        return content_hash in self._cache

    def _in_repository(self, content_hash: str) -> bool:
        try:
            return self.collector_storage.exists(content_hash)
        except Exception:
            return False
