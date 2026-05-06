"""
搜索 API 路由（全文检索/聚合/混合搜索）
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from ..services.query_router import query_router

bp = Blueprint('search', __name__, url_prefix='/api/v1/search')


@bp.route('/fulltext', methods=['POST'])
@jwt_required(optional=True)
def fulltext_search():
    """
    全文检索 API
    
    Request Body:
    {
        "keyword": "BlackRock",
        "index": "news_articles",
        "symbols": ["AAPL", "GOOGL"],
        "categories": ["technology"],
        "date_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "sentiment_range": {"gte": 0.5},
        "size": 10,
        "from": 0
    }
    """
    try:
        params = request.get_json()
        
        if not params or 'keyword' not in params:
            return jsonify({'error': 'keyword is required'}), 400
        
        result = query_router.execute('fulltext_search', params)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/company', methods=['POST'])
@jwt_required(optional=True)
def company_search():
    """
    公司搜索 API
    
    Request Body:
    {
        "keyword": "Apple",
        "sector": "Technology",
        "exchange": "NASDAQ",
        "size": 20
    }
    """
    try:
        params = request.get_json()
        
        if not params or 'keyword' not in params:
            return jsonify({'error': 'keyword is required'}), 400
        
        params['index'] = 'security_companies'
        result = query_router.execute('fulltext_search', params)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/institution', methods=['POST'])
@jwt_required(optional=True)
def institution_search():
    """
    机构搜索 API
    
    Request Body:
    {
        "keyword": "Vanguard",
        "institution_type": "fund",
        "country": "US"
    }
    """
    try:
        params = request.get_json()
        
        if not params or 'keyword' not in params:
            return jsonify({'error': 'keyword is required'}), 400
        
        params['index'] = 'institution_entities'
        result = query_router.execute('fulltext_search', params)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/hybrid', methods=['POST'])
@jwt_required(optional=True)
def hybrid_search():
    """
    混合搜索 API（ES + PG）
    
    Request Body:
    {
        "keyword": "Tesla",
        "table": "news_articles",
        "id_field": "article_id",
        "size": 10
    }
    """
    try:
        params = request.get_json()
        
        if not params or 'keyword' not in params:
            return jsonify({'error': 'keyword is required'}), 400
        
        result = query_router.execute('hybrid_search', params)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/aggregation', methods=['POST'])
@jwt_required(optional=True)
def aggregation():
    """
    聚合分析 API
    
    Request Body:
    {
        "index": "security_companies",
        "custom_aggs": {
            "avg_market_cap": {"avg": {"field": "market_cap"}}
        }
    }
    """
    try:
        params = request.get_json()
        
        result = query_router.execute('aggregation', params)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/exact', methods=['POST'])
@jwt_required(optional=True)
def exact_match():
    """
    精确查询 API
    
    Request Body:
    {
        "table": "news_articles",
        "conditions": {"id": 123},
        "limit": 100
    }
    """
    try:
        params = request.get_json()
        
        if not params or 'table' not in params:
            return jsonify({'error': 'table is required'}), 400
        
        result = query_router.execute('exact_match', params)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
