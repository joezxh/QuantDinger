"""Fast analysis graph enhancement patch helper."""
from app.services.graph_prompt_bridge import enrich_analysis_data_with_graph_context


def build_graph_enhanced_prompt_state(data, market: str, symbol: str, builder, logger):
    graph_ctx_text = ""
    graph_ctx = {}
    try:
        data, graph_ctx, graph_ctx_text = enrich_analysis_data_with_graph_context(
            data, market, symbol, builder
        )
        if graph_ctx_text:
            logger.info(f"Graph context enriched for {market}:{symbol}")
    except Exception as e:
        logger.debug(f"Graph context build failed (non-critical): {e}")
    return data, graph_ctx, graph_ctx_text
