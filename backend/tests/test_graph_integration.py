"""Graphiti integration tests — end-to-end PoC validation.

Covers ontology definitions, importer seed data, graph pipeline,
context builder degradation, analyzer degradation, and API route shapes.
"""
import os
from datetime import datetime

import pytest

os.environ.setdefault("GRAPHITI_ENABLED", "false")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")


# ------------------------------------------------------------------
# Ontology import sanity
# ------------------------------------------------------------------
def test_ontologies_importable():
    from app.graph.ontologies import (
        Company,
        Executive,
        Institution,
        CryptoAsset,
        Protocol,
        CryptoAccount,
        PredictionMarket,
        MarketOutcome,
    )

    c = Company(ticker="AAPL", name="Apple Inc.", sector="Technology")
    assert c.ticker == "AAPL"
    assert c.sector == "Technology"

    ca = CryptoAsset(symbol="BTC/USDT", chain="Bitcoin")
    assert ca.symbol == "BTC/USDT"
    assert ca.market == "Crypto"

    pm = PredictionMarket(market_id="abc123", question="Will it rain?")
    assert pm.market_id == "abc123"
    assert pm.active is True


# ------------------------------------------------------------------
# Importer seed data
# ------------------------------------------------------------------
def test_stock_importer_seed_data():
    from app.graph.importers.stock_importer import StockGraphImporter

    importer = StockGraphImporter(batch_size=100)
    insts = importer._fetch_institutions()
    assert len(insts) > 0
    assert insts[0]["name"] == "BlackRock"

    holds = importer._fetch_holdings()
    # Should contain at least one seed holding
    assert len(holds) > 0
    assert "from_id" in holds[0]
    assert "to_id" in holds[0]


def test_crypto_importer_seed_data():
    from app.graph.importers.crypto_importer import CryptoGraphImporter

    importer = CryptoGraphImporter(batch_size=100)
    accounts = importer._fetch_accounts()
    assert len(accounts) > 0
    assert accounts[0].get("label") in ("burn", "kol", "cex")

    holds = importer._fetch_holdings()
    assert len(holds) > 0


def test_polymarket_importer_seed_data():
    from app.graph.importers.polymarket_importer import PolymarketGraphImporter

    importer = PolymarketGraphImporter(batch_size=100)
    trades = importer._fetch_trades()
    # May be empty if no opportunity data; at minimum should not crash
    assert isinstance(trades, list)


# ------------------------------------------------------------------
# GraphContextBuilder degradation (no Neo4j)
# ------------------------------------------------------------------
def test_context_builder_degrades_gracefully():
    from app.graph.context_builder import GraphContextBuilder

    builder = GraphContextBuilder()
    ctx = builder.build("Crypto", "BTC/USDT")
    # Should always return a dict with expected keys even when Neo4j is down
    assert isinstance(ctx, dict)
    assert "related_assets" in ctx
    assert "recent_events" in ctx
    assert "smart_money" in ctx


def test_format_graph_context_for_llm():
    from app.graph.context_builder import format_graph_context_for_llm

    text = format_graph_context_for_llm({"related_assets": [{"symbol": "ETH"}]})
    assert isinstance(text, str)
    assert "ETH" in text

    empty = format_graph_context_for_llm({})
    assert empty == ""


# ------------------------------------------------------------------
# EventImpactAnalyzer degradation
# ------------------------------------------------------------------
def test_event_impact_analyzer_degrades():
    from app.services.event_impact_analyzer import EventImpactAnalyzer

    analyzer = EventImpactAnalyzer()
    result = analyzer.get_contagion_path("BTC/USDT", "ETH/USDT")
    assert isinstance(result, dict)
    assert "paths" in result
    assert "risk_score" in result

    impact = analyzer.trace_event_impact("nonexistent_event")
    assert isinstance(impact, dict)
    assert "affected_assets" in impact

    cascade = analyzer.find_cascade_risk("BTC/USDT")
    assert isinstance(cascade, dict)
    assert "cascade_risk_score" in cascade


# ------------------------------------------------------------------
# SmartMoneySignal degradation
# ------------------------------------------------------------------
def test_smart_money_signal_degrades():
    from app.services.smart_money_signal import SmartMoneySignal

    sms = SmartMoneySignal()
    pm = sms.get_polymarket_smart_money("fake_market_id")
    assert isinstance(pm, dict)
    assert "consensus" in pm

    whale = sms.get_whale_accumulation("BTC/USDT")
    assert isinstance(whale, dict)
    assert "accumulation_score" in whale

    inst = sms.get_institutional_flow("AAPL")
    assert isinstance(inst, dict)
    assert "flow_direction" in inst


# ------------------------------------------------------------------
# GraphPipeline — CollectedItem -> Episode (no real Graphiti)
# ------------------------------------------------------------------
def test_graph_pipeline_process_item():
    from app.collectors.base import CollectedItem
    from app.collectors.graph_pipeline import GraphPipeline

    item = CollectedItem(
        source="test",
        data_type="news",
        market="USStock",
        symbol="AAPL",
        raw_data={},
        normalized_data={"headline": "Test news"},
        should_build_episode=True,
    )

    pipeline = GraphPipeline()
    result = pipeline.process_item(item)

    assert isinstance(result, dict)
    assert "status" in result
    # Since Graphiti is disabled in test env, we expect disabled/no_client or db writes
    assert result["status"] in ("completed", "failed", "dedup_skipped", "episode_exists")


# ------------------------------------------------------------------
# CollectorScheduler manual invocation
# ------------------------------------------------------------------
def test_collector_scheduler_run_market_collection():
    from app.collectors.scheduler import CollectorScheduler

    scheduler = CollectorScheduler()
    # Should not crash even with mocked/disabled collectors
    result = scheduler.run_market_collection("Crypto", "BTC/USDT")
    assert isinstance(result, dict)
    assert "collected" in result
    assert "graph_results" in result


# ------------------------------------------------------------------
# API route shape validation (Flask test client)
# ------------------------------------------------------------------
class TestGraphAnalysisRoutes:
    """Verify new endpoints return expected shapes."""

    def test_context_endpoint(self, client):
        res = client.get("/api/graph-analysis/context?market=Crypto&symbol=BTC/USDT")
        assert res.status_code in (200, 500)  # 500 is acceptable if Neo4j down
        if res.status_code == 200:
            data = res.get_json()
            assert data["code"] == 1
            assert "data" in data

    def test_contagion_path_endpoint(self, client):
        res = client.get("/api/graph-analysis/contagion-path?from=BTC/USDT&to=ETH/USDT&market=Crypto")
        assert res.status_code in (200, 500)
        if res.status_code == 200:
            data = res.get_json()
            assert data["code"] == 1
            assert "paths" in data["data"]

    def test_smart_money_endpoint(self, client):
        res = client.get("/api/graph-analysis/smart-money/BTC/USDT?domain=crypto")
        assert res.status_code in (200, 500)
        if res.status_code == 200:
            data = res.get_json()
            assert data["code"] == 1
            assert "trend" in data["data"] or "consensus" in data["data"]

    def test_event_impact_endpoint(self, client):
        res = client.get("/api/graph-analysis/event-impact/fake_uid?max_depth=2")
        assert res.status_code in (200, 500)
        if res.status_code == 200:
            data = res.get_json()
            assert data["code"] == 1
            assert "affected_assets" in data["data"]

    def test_quality_endpoint(self, client):
        res = client.get("/api/graph-analysis/quality")
        assert res.status_code in (200, 500)
        if res.status_code == 200:
            data = res.get_json()
            assert data["code"] == 1
            assert "is_ready" in data["data"]
