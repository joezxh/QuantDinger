"""Domain graph API routes."""
from flask import Blueprint, jsonify, request

from app.services.crypto_graph_poc import CryptoGraphPocService
from app.services.domain_graph_services import CryptoGraphService, PolymarketGraphService, StockGraphService
from app.services.polymarket_graph_poc import PolymarketGraphPocService

stock_graph_bp = Blueprint("stock_graph", __name__)
crypto_graph_bp = Blueprint("crypto_graph", __name__)
polymarket_graph_bp = Blueprint("polymarket_graph", __name__)

stock_service = StockGraphService()
crypto_service = CryptoGraphService()
polymarket_service = PolymarketGraphService()
crypto_poc_service = CryptoGraphPocService()
polymarket_poc_service = PolymarketGraphPocService()


@stock_graph_bp.route("/company/<ticker>", methods=["GET"])
def get_stock_company_graph(ticker: str):
    """
    ---
    tags:
      - Knowledge Graph/Stock
    summary: "Get stock company graph"
    description: "Return the knowledge graph for a stock company including shareholders, subsidiaries, competitors, and related entities."
    produces:
      - application/json
    parameters:
      - name: ticker
        in: path
        type: string
        required: true
        description: "Stock ticker symbol (e.g. AAPL)"
    responses:
      200:
        description: Successful response with company graph data
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
    return jsonify({"code": 1, "msg": "success", "data": stock_service.get_company_graph(ticker.upper())})


@crypto_graph_bp.route("/asset/<path:symbol>", methods=["GET"])
def get_crypto_asset_graph(symbol: str):
    """
    ---
    tags:
      - Knowledge Graph/Crypto
    summary: "Get crypto asset graph"
    description: "Return the knowledge graph for a cryptocurrency asset including related projects and token relationships."
    produces:
      - application/json
    parameters:
      - name: symbol
        in: path
        type: string
        required: true
        description: "Trading symbol (e.g. BTC, ETH)"
    responses:
      200:
        description: Successful response with crypto graph data
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
    return jsonify({"code": 1, "msg": "success", "data": crypto_service.get_asset_graph(symbol)})


@crypto_graph_bp.route("/poc/run", methods=["POST"])
def run_crypto_graph_poc():
    """
    ---
    tags:
      - Knowledge Graph/Crypto
    summary: "Run crypto graph PoC"
    description: "Execute the cryptocurrency knowledge graph proof-of-concept pipeline."
    produces:
      - application/json
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            symbol:
              type: string
              default: ETH/USDT
              description: "Trading pair symbol"
    responses:
      200:
        description: PoC execution completed
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
    data = request.get_json() or {}
    symbol = data.get("symbol") or "ETH/USDT"
    return jsonify({"code": 1, "msg": "success", "data": crypto_poc_service.run(symbol=symbol)})


@polymarket_graph_bp.route("/market/<market_id>", methods=["GET"])
def get_polymarket_market_graph(market_id: str):
    """
    ---
    tags:
      - Knowledge Graph/Polymarket
    summary: "Get Polymarket market graph"
    description: "Return the knowledge graph for a Polymarket prediction market including related events and outcomes."
    produces:
      - application/json
    parameters:
      - name: market_id
        in: path
        type: string
        required: true
        description: "Polymarket market ID"
    responses:
      200:
        description: Successful response with market graph data
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
    return jsonify({"code": 1, "msg": "success", "data": polymarket_service.get_market_graph(market_id)})


@polymarket_graph_bp.route("/poc/run", methods=["POST"])
def run_polymarket_graph_poc():
    """
    ---
    tags:
      - Knowledge Graph/Polymarket
    summary: "Run Polymarket graph PoC"
    description: "Execute the Polymarket prediction market knowledge graph proof-of-concept pipeline."
    produces:
      - application/json
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            market_id:
              type: string
              default: "12345"
              description: "Polymarket market ID"
    responses:
      200:
        description: PoC execution completed
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
    data = request.get_json() or {}
    market_id = str(data.get("market_id") or "12345")
    return jsonify({"code": 1, "msg": "success", "data": polymarket_poc_service.run(market_id=market_id)})
