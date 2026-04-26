"""Collector registry and lazy factory helpers."""
from app.services.market_data_collector import get_market_data_collector


class CollectorRegistry:
    def __init__(self):
        self._collectors = {
            "market_data": get_market_data_collector,
        }

    def get(self, name: str):
        factory = self._collectors.get(name)
        return factory() if factory else None

    def names(self):
        return list(self._collectors.keys())
