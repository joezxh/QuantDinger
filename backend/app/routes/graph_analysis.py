"""Graph analysis API routes — generic graph context and ingestion endpoints."""
from flask import Blueprint, jsonify, request

from app.graph.context_builder import GraphContextBuilder, format_graph_context_for_llm
from app.graph.connection import run_cypher
from app.graph.quality_monitor import GraphQualityMonitor
from app.services.event_impact_analyzer import EventImpactAnalyzer
from app.services.smart_money_signal import SmartMoneySignal
from app.utils.logger import get_logger

logger = get_logger(__name__)
graph_analysis_bp = Blueprint("graph_analysis", __name__)

_context_builder = GraphContextBuilder()
_quality_monitor = GraphQualityMonitor()
_event_analyzer = EventImpactAnalyzer()
_smart_money = SmartMoneySignal()


@graph_analysis_bp.route("/context", methods=["GET"])
def get_graph_context():
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Get graph context"
    description: "Retrieve structured knowledge graph context for a trading symbol, including related entities and relationships."
    produces:
      - application/json
    parameters:
      - name: market
        in: query
        type: string
        required: true
        description: "Market type (e.g. USStock, Crypto)"
      - name: symbol
        in: query
        type: string
        required: true
        description: "Trading symbol"
    responses:
      200:
        description: Successful response with graph context
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
      400:
        description: Missing required parameters
      500:
        description: Internal Server Error
    """
    market = request.args.get("market", "")
    symbol = request.args.get("symbol", "")
    if not market or not symbol:
        return jsonify({"code": 0, "msg": "market and symbol are required"}), 400

    try:
        ctx = _context_builder.build(market, symbol)
        return jsonify({"code": 1, "msg": "success", "data": ctx})
    except Exception as e:
        logger.warning("Graph context build failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500


@graph_analysis_bp.route("/context/llm", methods=["GET"])
def get_graph_context_llm():
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Get LLM-formatted graph context"
    description: "Return graph context formatted as LLM-ready text for use in AI prompts."
    produces:
      - application/json
    parameters:
      - name: market
        in: query
        type: string
        required: true
        description: "Market type"
      - name: symbol
        in: query
        type: string
        required: true
        description: "Trading symbol"
    responses:
      200:
        description: Successful response with LLM-formatted context
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
              properties:
                text:
                  type: string
                raw:
                  type: object
      400:
        description: Missing required parameters
      500:
        description: Internal Server Error
    """
    market = request.args.get("market", "")
    symbol = request.args.get("symbol", "")
    if not market or not symbol:
        return jsonify({"code": 0, "msg": "market and symbol are required"}), 400

    try:
        ctx = _context_builder.build(market, symbol)
        text = format_graph_context_for_llm(ctx)
        return jsonify({"code": 1, "msg": "success", "data": {"text": text, "raw": ctx}})
    except Exception as e:
        logger.warning("Graph context LLM format failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500


@graph_analysis_bp.route("/related", methods=["GET"])
def get_related_assets():
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Find related assets"
    description: "Query the knowledge graph to find assets related to a given symbol."
    produces:
      - application/json
    parameters:
      - name: market
        in: query
        type: string
        required: false
        description: "Market type filter"
      - name: symbol
        in: query
        type: string
        required: true
        description: "Trading symbol"
    responses:
      200:
        description: Successful response with related assets
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
      400:
        description: Missing symbol parameter
      500:
        description: Internal Server Error
    """
    market = request.args.get("market", "")
    symbol = request.args.get("symbol", "")
    if not symbol:
        return jsonify({"code": 0, "msg": "symbol is required"}), 400

    try:
        from app.graph.queries import find_related_assets
        data = find_related_assets(symbol, market)
        return jsonify({"code": 1, "msg": "success", "data": data})
    except Exception as e:
        logger.warning("Related assets query failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500


@graph_analysis_bp.route("/events", methods=["GET"])
def get_recent_events():
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Get recent events"
    description: "Retrieve recent graph events affecting a given trading symbol."
    produces:
      - application/json
    parameters:
      - name: symbol
        in: query
        type: string
        required: true
        description: "Trading symbol"
      - name: limit
        in: query
        type: integer
        required: false
        default: 5
        description: "Max number of events to return"
    responses:
      200:
        description: Successful response with recent events
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
      400:
        description: Missing symbol parameter
      500:
        description: Internal Server Error
    """
    symbol = request.args.get("symbol", "")
    limit = request.args.get("limit", 5, type=int)
    if not symbol:
        return jsonify({"code": 0, "msg": "symbol is required"}), 400

    try:
        from app.graph.queries import get_recent_events
        data = get_recent_events(symbol, limit)
        return jsonify({"code": 1, "msg": "success", "data": data})
    except Exception as e:
        logger.warning("Recent events query failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500


@graph_analysis_bp.route("/cypher", methods=["POST"])
def run_custom_cypher():
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Execute custom Cypher query"
    description: "Execute a read-only Cypher query against the knowledge graph (for debugging/management). Write operations are rejected."
    produces:
      - application/json
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - query
          properties:
            query:
              type: string
              description: "Cypher query statement"
            params:
              type: object
              description: "Query parameters"
    responses:
      200:
        description: Successful response with query results
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
      400:
        description: Missing query
      403:
        description: Write operations not allowed
      500:
        description: Internal Server Error
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    params = data.get("params", {})

    if not query:
        return jsonify({"code": 0, "msg": "query is required"}), 400

    # Safety: reject write operations
    upper = query.upper()
    if any(kw in upper for kw in ("CREATE", "DELETE", "DROP", "SET", "MERGE", "REMOVE")):
        return jsonify({"code": 0, "msg": "Write operations are not allowed"}), 403

    try:
        result = run_cypher(query, params)
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.warning("Custom Cypher failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500


@graph_analysis_bp.route("/quality", methods=["GET"])
def get_graph_quality():
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Get graph quality report"
    description: "Return data quality and readiness report for the knowledge graph."
    produces:
      - application/json
    responses:
      200:
        description: Successful response with quality report
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
      500:
        description: Internal Server Error
    """
    try:
        report = _quality_monitor.check_readiness()
        return jsonify({"code": 1, "msg": "success", "data": report})
    except Exception as e:
        logger.warning("Quality check failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500


@graph_analysis_bp.route("/contagion-path", methods=["GET"])
def get_contagion_path():
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Asset contagion path"
    description: "Query multi-hop transmission paths between two assets in the knowledge graph."
    produces:
      - application/json
    parameters:
      - name: from
        in: query
        type: string
        required: true
        description: "Source symbol"
      - name: to
        in: query
        type: string
        required: true
        description: "Target symbol"
      - name: market
        in: query
        type: string
        required: false
        default: "Crypto"
        description: "Market domain"
    responses:
      200:
        description: Successful response with path list and risk score
      400:
        description: Missing parameters
      500:
        description: Internal Server Error
    """
    from_symbol = request.args.get("from", "").strip()
    to_symbol = request.args.get("to", "").strip()
    market = request.args.get("market", "Crypto").strip()
    if not from_symbol or not to_symbol:
        return jsonify({"code": 0, "msg": "from and to are required"}), 400

    try:
        data = _event_analyzer.get_contagion_path(from_symbol, to_symbol, market=market)
        return jsonify({"code": 1, "msg": "success", "data": data})
    except Exception as e:
        logger.warning("Contagion path query failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500


@graph_analysis_bp.route("/smart-money/<symbol>", methods=["GET"])
def get_smart_money(symbol):
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Smart money signals"
    description: "Aggregate smart-money signals for a symbol across Polymarket, crypto whales, and stock institutions."
    produces:
      - application/json
    parameters:
      - name: symbol
        in: path
        type: string
        required: true
        description: "Trading symbol or market_id"
      - name: domain
        in: query
        type: string
        required: false
        default: "auto"
        description: "Domain override: polymarket | crypto | stock | auto"
    responses:
      200:
        description: Successful response with signal aggregation
      400:
        description: Missing symbol
      500:
        description: Internal Server Error
    """
    domain = request.args.get("domain", "auto").strip().lower()
    symbol = symbol.strip()
    if not symbol:
        return jsonify({"code": 0, "msg": "symbol is required"}), 400

    try:
        # Auto-detect domain by symbol shape
        if domain == "auto":
            if "/" in symbol or symbol.upper() in ("BTC", "ETH", "BNB", "SOL"):
                domain = "crypto"
            elif symbol.startswith("0x") and len(symbol) >= 42:
                domain = "polymarket"
            else:
                domain = "stock"

        if domain == "polymarket":
            data = _smart_money.get_polymarket_smart_money(symbol)
        elif domain == "crypto":
            data = _smart_money.get_whale_accumulation(symbol)
        else:
            data = _smart_money.get_institutional_flow(symbol)
        return jsonify({"code": 1, "msg": "success", "data": data})
    except Exception as e:
        logger.warning("Smart money query failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500


@graph_analysis_bp.route("/event-impact/<event_uid>", methods=["GET"])
def get_event_impact(event_uid):
    """
    ---
    tags:
      - Knowledge Graph/Analysis
    summary: "Event impact chain"
    description: "Trace how a single event ripples through the knowledge graph."
    produces:
      - application/json
    parameters:
      - name: event_uid
        in: path
        type: string
        required: true
        description: "Event unique identifier"
      - name: max_depth
        in: query
        type: integer
        required: false
        default: 3
        description: "Max traversal depth"
    responses:
      200:
        description: Successful response with affected assets and events
      400:
        description: Missing event_uid
      500:
        description: Internal Server Error
    """
    event_uid = event_uid.strip()
    max_depth = request.args.get("max_depth", 3, type=int)
    if not event_uid:
        return jsonify({"code": 0, "msg": "event_uid is required"}), 400

    try:
        data = _event_analyzer.trace_event_impact(event_uid, max_depth=max_depth)
        return jsonify({"code": 1, "msg": "success", "data": data})
    except Exception as e:
        logger.warning("Event impact query failed: %s", e)
        return jsonify({"code": 0, "msg": str(e)}), 500
