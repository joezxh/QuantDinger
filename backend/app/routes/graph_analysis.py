"""Graph analysis API routes — generic graph context and ingestion endpoints."""
from flask import Blueprint, jsonify, request

from app.graph.context_builder import GraphContextBuilder, format_graph_context_for_llm
from app.graph.connection import run_cypher
from app.graph.quality_monitor import GraphQualityMonitor
from app.utils.logger import get_logger

logger = get_logger(__name__)
graph_analysis_bp = Blueprint("graph_analysis", __name__)

_context_builder = GraphContextBuilder()
_quality_monitor = GraphQualityMonitor()


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
