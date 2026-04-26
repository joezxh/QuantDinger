"""Runnable stock news graph PoC script."""
from pathlib import Path
from pprint import pprint
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.stock_news_graph_poc import StockNewsGraphPocService


if __name__ == "__main__":
    service = StockNewsGraphPocService()
    result = service.run(symbol="NVDA", market="USStock")
    pprint(result)
