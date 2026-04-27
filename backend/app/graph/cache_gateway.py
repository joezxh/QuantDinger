"""Cache gateway for graph-related Redis keys."""
from app.utils.cache import CacheManager


class GraphCacheGateway:
    def __init__(self):
        self.cache = CacheManager()

    def get_context(self, market: str, symbol: str):
        return self.cache.get(f"graph:context:{market}:{symbol}")

    def set_context(self, market: str, symbol: str, value, ttl: int = 300):
        self.cache.set(f"graph:context:{market}:{symbol}", value, ttl=ttl)

    def get_subgraph(self, domain: str, entity: str):
        return self.cache.get(f"graph:subgraph:{domain}:{entity}")

    def set_subgraph(self, domain: str, entity: str, value, ttl: int = 600):
        self.cache.set(f"graph:subgraph:{domain}:{entity}", value, ttl=ttl)

    def get_task_status(self, job_id: str):
        return self.cache.get(f"graph:task:status:{job_id}")

    def set_task_status(self, job_id: str, value, ttl: int = 3600):
        self.cache.set(f"graph:task:status:{job_id}", value, ttl=ttl)
