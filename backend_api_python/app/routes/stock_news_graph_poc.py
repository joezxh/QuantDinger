"""Stock news graph PoC API route."""
from flask import Blueprint, jsonify, request

from app.services.stock_news_graph_poc import StockNewsGraphPocService

stock_news_graph_poc_bp = Blueprint("stock_news_graph_poc", __name__)
service = StockNewsGraphPocService()


@stock_news_graph_poc_bp.route("/run", methods=["POST"])
def run_stock_news_graph_poc():
    """
    ---
    tags:
      - Knowledge Graph/Stock
    summary: "Run stock news graph PoC"
    description: "Execute the stock news knowledge graph proof-of-concept pipeline for a given symbol."
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
              default: NVDA
              description: "Stock ticker symbol"
            market:
              type: string
              default: USStock
              description: "Market type"
    responses:
      200:
        description: PoC execution completed successfully
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
    symbol = (data.get("symbol") or "NVDA").strip().upper()
    market = (data.get("market") or "USStock").strip()
    result = service.run(symbol=symbol, market=market)
    return jsonify({"code": 1, "msg": "success", "data": result})
