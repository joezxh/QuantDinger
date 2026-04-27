"""Compatibility helper for graph-aware analysis prompt injection."""
from app.graph.context_builder import format_graph_context_for_llm


def enrich_analysis_data_with_graph_context(data, market: str, symbol: str, builder):
    graph_ctx_text = ""
    graph_ctx = {}
    if not builder:
        return data, graph_ctx, graph_ctx_text

    graph_ctx = builder.build(market, symbol)
    graph_ctx_text = format_graph_context_for_llm(graph_ctx)
    data["graph_context"] = graph_ctx
    if graph_ctx_text:
        original_summary = str(data.get("summary") or "").strip()
        data["summary"] = f"{original_summary}\n{graph_ctx_text}".strip() if original_summary else graph_ctx_text
    return data, graph_ctx, graph_ctx_text
