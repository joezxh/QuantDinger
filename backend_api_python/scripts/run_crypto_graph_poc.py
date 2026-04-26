"""Runnable crypto graph PoC script."""
from pathlib import Path
from pprint import pprint
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.crypto_graph_poc import CryptoGraphPocService


if __name__ == "__main__":
    service = CryptoGraphPocService()
    result = service.run(symbol="ETH/USDT")
    pprint(result)
