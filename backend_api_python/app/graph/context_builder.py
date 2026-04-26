"""Graph context builder with cache-first behavior."""
from typing import Dict

from app.graph.cache_gateway import GraphCacheGateway
from app.graph.queries import (
    find_related_assets,
    get_crypto_kol_consensus,
    get_polymarket_smart_money,
    get_prediction_market_signals,
    get_recent_events,
    get_stock_holders,
)


class GraphContextBuilder:
    def __init__(self):
        self.cache = GraphCacheGateway()

    def build(self, market: str, symbol: str) -> Dict:
        cached = self.cache.get_context(market, symbol)
        if cached:
            return cached

        ctx = self._build_fresh(market, symbol)
        self.cache.set_context(market, symbol, ctx, ttl=300)
        return ctx

    def _build_fresh(self, market: str, symbol: str) -> Dict:
        market_normalized = (market or "").lower()
        related_assets = find_related_assets(symbol, market) if symbol else []
        recent_events = get_recent_events(symbol) if symbol else []
        prediction_market_signals = get_prediction_market_signals(symbol) if symbol else []

        ctx = {
            "related_assets": related_assets or [],
            "recent_events": recent_events or [],
            "impact_chain": [],
            "narrative_drift": {},
            "top_institutional_holders": [],
            "kol_consensus": {},
            "prediction_market_signals": prediction_market_signals or [],
            "smart_money": {},
            "subgraph_summary": self._build_summary(market, symbol, related_assets, recent_events, prediction_market_signals),
        }

        if market_normalized in {"usstock", "hkstock", "cnstock", "stock"}:
            ctx["top_institutional_holders"] = get_stock_holders(symbol)
        elif market_normalized == "crypto":
            kol = get_crypto_kol_consensus(symbol)
            ctx["kol_consensus"] = kol[0] if kol else {}
        elif market_normalized == "polymarket":
            market_id = symbol.split(":", 1)[-1] if ":" in symbol else symbol
            ctx["smart_money"] = {"top_users": get_polymarket_smart_money(market_id)}
            ctx["prediction_market_signals"] = prediction_market_signals or []

        return ctx

    def _build_summary(self, market: str, symbol: str, related_assets, recent_events, prediction_market_signals) -> str:
        parts = [f"{market}:{symbol}"]
        if related_assets:
            parts.append(f"related_assets={len(related_assets)}")
        if recent_events:
            parts.append(f"recent_events={len(recent_events)}")
        if prediction_market_signals:
            parts.append(f"pm_signals={len(prediction_market_signals)}")
        if len(parts) == 1:
            parts.append("no_graph_data")
        return ", ".join(parts)


def format_graph_context_for_llm(ctx: Dict) -> str:
    if not ctx:
        return ""

    parts = ["【知识图谱增强信息】"]

    if ctx.get("related_assets"):
        parts.append("关联资产：" + ", ".join([x.get("symbol", "") for x in ctx["related_assets"][:5]]))

    if ctx.get("recent_events"):
        parts.append("近期事件：" + "；".join([x.get("title", "") for x in ctx["recent_events"][:3] if x.get("title")]))

    if ctx.get("top_institutional_holders"):
        holders = [x.get("institution", "") for x in ctx["top_institutional_holders"][:3]]
        parts.append("主要机构股东：" + ", ".join(holders))

    if ctx.get("kol_consensus"):
        parts.append(f"KOL 共识：{ctx['kol_consensus']}")

    if ctx.get("smart_money"):
        parts.append(f"聪明钱：{ctx['smart_money']}")

    if ctx.get("prediction_market_signals"):
        for pm in ctx["prediction_market_signals"][:2]:
            probability = pm.get("probability", 50)
            try:
                probability_text = f"{float(probability):.1f}%"
            except Exception:
                probability_text = str(probability)
            parts.append(f"预测市场：{pm.get('question', '')[:60]}（概率 {probability_text}）")

    if ctx.get("subgraph_summary"):
        parts.append(f"子图摘要：{ctx['subgraph_summary']}")

    return "\n".join(parts) if len(parts) > 1 else ""
