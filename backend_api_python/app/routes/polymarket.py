"""Polymarket预测市场API路由
提供按需分析接口（只读，不涉及交易）
"""
from flask import Blueprint, jsonify, request, g

from app.utils.auth import login_required
from app.utils.logger import get_logger
from app.data_sources.polymarket import PolymarketDataSource
from app.database.repositories.polymarket_route_repository import PolymarketRouteRepository
from app.database.session import get_session
import re
import json

logger = get_logger(__name__)
polymarket_bp = Blueprint('polymarket', __name__)
polymarket_source = PolymarketDataSource()


@polymarket_bp.route("/analyze", methods=["POST"])
@login_required
def analyze_polymarket():
    """
    ---
    tags:
      - Market/Polymarket
    summary: "Analyze Polymarket prediction market"
    description: "Search and analyze a Polymarket prediction market by URL or title, returning AI analysis results."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - input
          properties:
            input:
              type: string
              description: "Polymarket URL or market title"
            language:
              type: string
              default: zh-CN
              description: "Analysis language"
            model:
              type: string
              description: "LLM model (optional)"
    responses:
      200:
        description: Success
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
        description: Bad Request - Missing input or invalid market
      401:
        description: Unauthorized
      404:
        description: Market not found
      500:
        description: Internal Server Error
    """
    try:
        from app.services.billing_service import BillingService
        from app.services.polymarket_analyzer import PolymarketAnalyzer
        from decimal import Decimal
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({"code": 0, "msg": "User not authenticated", "data": None}), 401
        data = request.get_json() or {}
        input_text = (data.get('input') or '').strip()
        language = data.get('language', 'zh-CN')
        if not input_text:
            return jsonify({"code": 0, "msg": "Input is required (Polymarket URL or market title)", "data": None}), 400
        market_id = None
        slug = None
        for pattern in [r'polymarket\.com/event/([^/?]+)', r'polymarket\.com/markets/(\d+)', r'polymarket\.com/market/(\d+)']:
            match = re.search(pattern, input_text)
            if match:
                extracted = match.group(1)
                if extracted.isdigit():
                    market_id = extracted
                else:
                    slug = extracted
                break
        if not market_id and not slug:
            search_results = polymarket_source.search_markets(input_text, limit=5)
            if search_results:
                market_id = search_results[0].get('market_id')
        if not market_id and not slug:
            return jsonify({"code": 0, "msg": "Could not parse market ID or slug from input. Please provide a valid Polymarket URL or market title.", "data": None}), 400
        market = polymarket_source.get_market_details(market_id) if market_id else None
        if not market and slug:
            search_results = polymarket_source.search_markets(slug, limit=10)
            for result in search_results:
                if result.get('slug') == slug or slug in (result.get('question') or ''):
                    market = result
                    market_id = result.get('market_id')
                    break
            if not market and search_results:
                market = search_results[0]
                market_id = market.get('market_id')
        if not market:
            return jsonify({"code": 0, "msg": "Market not found. Please check the URL or title.", "data": None}), 404
        if not market_id:
            market_id = market.get('market_id')
        if not market_id:
            return jsonify({"code": 0, "msg": "Invalid market data", "data": None}), 400
        billing = BillingService()
        cost = 0
        if billing.is_billing_enabled():
            cost = billing.get_feature_cost('polymarket_deep_analysis')
            if cost > 0:
                user_credits = billing.get_user_credits(user_id)
                if user_credits < Decimal(str(cost)):
                    return jsonify({"code": 0, "msg": "Insufficient credits", "data": {"required": cost, "current": float(user_credits), "shortage": float(Decimal(str(cost)) - user_credits)}}), 400
                success, error_msg = billing.check_and_consume(user_id=user_id, feature='polymarket_deep_analysis', reference_id=f"polymarket_{market_id}")
                if not success:
                    return jsonify({"code": 0, "msg": f"Failed to deduct credits: {error_msg}", "data": None}), 500
        analyzer = PolymarketAnalyzer()
        analysis_result = analyzer.analyze_market(market_id, user_id=user_id, use_cache=False, language=language, model=data.get('model'))
        if analysis_result.get('error'):
            return jsonify({"code": 0, "msg": analysis_result.get('error', 'Analysis failed'), "data": None}), 500
        remaining_credits = float(billing.get_user_credits(user_id)) if billing.is_billing_enabled() else 0
        return jsonify({"code": 1, "msg": "success", "data": {"market": market, "analysis": analysis_result, "credits_charged": cost, "remaining_credits": remaining_credits}})
    except Exception as e:
        logger.error(f"Polymarket analyze API failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e), "data": None}), 500


@polymarket_bp.route("/history", methods=["GET"])
@login_required
def get_polymarket_history():
    """
    ---
    tags:
      - Market/Polymarket
    summary: "Get Polymarket analysis history"
    description: "Return the current user's Polymarket market analysis history with pagination."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: "Page number"
      - name: page_size
        in: query
        type: integer
        required: false
        default: 20
        description: "Items per page, max 100"
    responses:
      200:
        description: Success
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
                items:
                  type: array
                total:
                  type: integer
                page:
                  type: integer
                page_size:
                  type: integer
      401:
        description: Unauthorized
      500:
        description: Internal Server Error
    """
    try:
        user_id = g.user_id
        page = request.args.get('page', 1, type=int)
        page_size = min(request.args.get('page_size', 20, type=int), 100)
        offset = (page - 1) * page_size
        with get_session() as session:
            repo = PolymarketRouteRepository(session)
            total = repo.count_user_history(user_id)
            rows = repo.list_user_history(user_id, page_size, offset)
        items = []
        for row in rows:
            try:
                result_data = json.loads(row.result_json) if row.result_json else {}
            except Exception:
                result_data = {}
            market_data = result_data.get('market', {})
            analysis_data = result_data.get('analysis', {})
            items.append({
                'id': row.id,
                'market_id': row.symbol,
                'market_title': market_data.get('question') or market_data.get('title') or f"Market {row.symbol}",
                'market_url': market_data.get('polymarket_url'),
                'ai_predicted_probability': analysis_data.get('ai_predicted_probability'),
                'market_probability': analysis_data.get('market_probability'),
                'recommendation': analysis_data.get('recommendation'),
                'opportunity_score': analysis_data.get('opportunity_score'),
                'confidence_score': analysis_data.get('confidence_score'),
                'status': row.status,
                'created_at': row.created_at.isoformat() if row.created_at else None,
                'completed_at': row.completed_at.isoformat() if getattr(row, 'completed_at', None) else None,
            })
        return jsonify({"code": 1, "msg": "success", "data": {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": (total + page_size - 1) // page_size}})
    except Exception as e:
        logger.error(f"Get Polymarket history failed: {e}", exc_info=True)
        return jsonify({"code": 0, "msg": str(e), "data": None}), 500
