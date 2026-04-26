"""Runnable polymarket graph PoC script."""
from pathlib import Path
from pprint import pprint
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.polymarket_graph_poc import PolymarketGraphPocService


if __name__ == "__main__":
    service = PolymarketGraphPocService()
    result = service.run(market_id="12345")
    pprint(result)
