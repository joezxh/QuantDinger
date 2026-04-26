"""Runnable graph smoke script."""
from pathlib import Path
from pprint import pprint
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.graph_feature_smoke import GraphFeatureSmoke


if __name__ == "__main__":
    pprint(GraphFeatureSmoke().run())
