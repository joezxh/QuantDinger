"""
Community APIs - 指标社区接口

提供指标市场、购买、评论等功能的 REST API。
"""

from flask import Blueprint, jsonify, request, g

from app.utils.auth import login_required
from app.utils.logger import get_logger
from app.services.community_service import get_community_service

logger = get_logger(__name__)

community_bp = Blueprint("community", __name__)


# ==========================================
# 指标市场
# ==========================================

@community_bp.route("/indicators", methods=["GET"])
@login_required
def get_market_indicators():
    """
    ---
    tags:
      - General
    summary: "获取市场指标列表"
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        type: string
        required: false
        description: "Page"
      - name: page_size
        in: query
        type: string
        required: false
        description: "Page Size"
      - name: keyword
        in: query
        type: string
        required: false
        description: "Keyword"
      - name: pricing_type
        in: query
        type: string
        required: false
        description: "Pricing Type"
      - name: sort_by
        in: query
        type: string
        required: false
        description: "Sort By"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 12))
        keyword = request.args.get('keyword', '').strip()
        pricing_type = request.args.get('pricing_type', '').strip() or None
        sort_by = request.args.get('sort_by', 'newest').strip()
        
        # 限制每页数量
        page_size = min(max(page_size, 1), 50)
        
        service = get_community_service()
        result = service.get_market_indicators(
            page=page,
            page_size=page_size,
            keyword=keyword if keyword else None,
            pricing_type=pricing_type,
            sort_by=sort_by,
            user_id=g.user_id
        )
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"get_market_indicators failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/indicators/<int:indicator_id>", methods=["GET"])
@login_required
def get_indicator_detail(indicator_id: int):
    """
    ---
    tags:
      - General
    summary: "获取指标详情"
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        service = get_community_service()
        result = service.get_indicator_detail(indicator_id, user_id=g.user_id)
        
        if not result:
            return jsonify({'code': 0, 'msg': 'indicator_not_found', 'data': None}), 404
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"get_indicator_detail failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


# ==========================================
# 购买功能
# ==========================================

@community_bp.route("/indicators/<int:indicator_id>/purchase", methods=["POST"])
@login_required
def purchase_indicator(indicator_id: int):
    """
    ---
    tags:
      - Purchase
    summary: "购买指标"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        service = get_community_service()
        success, message, data = service.purchase_indicator(
            buyer_id=g.user_id,
            indicator_id=indicator_id
        )
        
        if success:
            return jsonify({'code': 1, 'msg': message, 'data': data})
        else:
            return jsonify({'code': 0, 'msg': message, 'data': data}), 400
            
    except Exception as e:
        logger.error(f"purchase_indicator failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/indicators/<int:indicator_id>/sync", methods=["POST"])
@login_required
def sync_purchased_indicator(indicator_id: int):
    """
    ---
    tags:
      - Sync
    summary: "同步已购买指标的最新代码"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        service = get_community_service()
        success, message, data = service.sync_purchased_indicator(
            buyer_id=g.user_id,
            indicator_id=indicator_id
        )

        if success:
            return jsonify({'code': 1, 'msg': message, 'data': data})
        else:
            # 不同失败场景给到可区分的 http 状态，便于前端处理
            status = 400
            if message in ('indicator_not_found', 'indicator_unpublished', 'local_copy_not_found'):
                status = 404
            elif message == 'not_purchased':
                status = 403
            return jsonify({'code': 0, 'msg': message, 'data': data}), status

    except Exception as e:
        logger.error(f"sync_purchased_indicator failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/my-purchases", methods=["GET"])
@login_required
def get_my_purchases():
    """
    ---
    tags:
      - General
    summary: "获取我购买的指标列表"
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        type: string
        required: false
        description: "Page"
      - name: page_size
        in: query
        type: string
        required: false
        description: "Page Size"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        page_size = min(max(page_size, 1), 50)
        
        service = get_community_service()
        result = service.get_my_purchases(
            user_id=g.user_id,
            page=page,
            page_size=page_size
        )
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"get_my_purchases failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


# ==========================================
# 评论功能
# ==========================================

@community_bp.route("/indicators/<int:indicator_id>/comments", methods=["GET"])
@login_required
def get_comments(indicator_id: int):
    """
    ---
    tags:
      - General
    summary: "获取指标评论列表"
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
      - name: page
        in: query
        type: string
        required: false
        description: "Page"
      - name: page_size
        in: query
        type: string
        required: false
        description: "Page Size"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        page_size = min(max(page_size, 1), 50)
        
        service = get_community_service()
        result = service.get_comments(
            indicator_id=indicator_id,
            page=page,
            page_size=page_size
        )
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"get_comments failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/indicators/<int:indicator_id>/comments", methods=["POST"])
@login_required
def add_comment(indicator_id: int):
    """
    ---
    tags:
      - Add
    summary: "添加评论"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
      - name: body
        in: body
        schema:
          type: object
          properties:
            rating:
              type: string
            content:
              type: string
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json() or {}
        rating = int(data.get('rating', 5))
        content = (data.get('content') or '').strip()
        
        service = get_community_service()
        success, message, result = service.add_comment(
            user_id=g.user_id,
            indicator_id=indicator_id,
            rating=rating,
            content=content
        )
        
        if success:
            return jsonify({'code': 1, 'msg': message, 'data': result})
        else:
            return jsonify({'code': 0, 'msg': message, 'data': result}), 400
            
    except Exception as e:
        logger.error(f"add_comment failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/indicators/<int:indicator_id>/comments/<int:comment_id>", methods=["PUT"])
@login_required
def update_comment(indicator_id: int, comment_id: int):
    """
    ---
    tags:
      - General
    summary: "更新评论（只能修改自己的评论）"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
      - name: comment_id
        in: path
        type: integer
        required: true
        description: "Comment Id"
      - name: body
        in: body
        schema:
          type: object
          properties:
            rating:
              type: string
            content:
              type: string
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json() or {}
        rating = int(data.get('rating', 5))
        content = (data.get('content') or '').strip()
        
        service = get_community_service()
        success, message, result = service.update_comment(
            user_id=g.user_id,
            comment_id=comment_id,
            indicator_id=indicator_id,
            rating=rating,
            content=content
        )
        
        if success:
            return jsonify({'code': 1, 'msg': message, 'data': result})
        else:
            return jsonify({'code': 0, 'msg': message, 'data': result}), 400
            
    except Exception as e:
        logger.error(f"update_comment failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/indicators/<int:indicator_id>/my-comment", methods=["GET"])
@login_required
def get_my_comment(indicator_id: int):
    """
    ---
    tags:
      - General
    summary: "获取当前用户对指定指标的评论（用于编辑）"
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        service = get_community_service()
        result = service.get_user_comment(
            user_id=g.user_id,
            indicator_id=indicator_id
        )
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"get_my_comment failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


# ==========================================
# 实盘表现
# ==========================================

@community_bp.route("/indicators/<int:indicator_id>/performance", methods=["GET"])
@login_required
def get_indicator_performance(indicator_id: int):
    """
    ---
    tags:
      - General
    summary: "获取指标的实盘表现统计"
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        service = get_community_service()
        result = service.get_indicator_performance(indicator_id)
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"get_indicator_performance failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


# ==========================================
# 管理员审核功能
# ==========================================

def _is_admin():
    """检查当前用户是否是管理员"""
    role = getattr(g, 'user_role', None)
    return role == 'admin'


@community_bp.route("/admin/pending-indicators", methods=["GET"])
@login_required
def get_pending_indicators():
    """
    ---
    tags:
      - General
    summary: "获取待审核的指标列表（管理员专用）"
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        type: string
        required: false
        description: "Page"
      - name: page_size
        in: query
        type: string
        required: false
        description: "Page Size"
      - name: review_status
        in: query
        type: string
        required: false
        description: "Review Status"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        if not _is_admin():
            return jsonify({'code': 0, 'msg': 'admin_required', 'data': None}), 403
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        review_status = request.args.get('review_status', 'pending').strip() or 'pending'
        page_size = min(max(page_size, 1), 100)
        
        service = get_community_service()
        result = service.get_pending_indicators(
            page=page,
            page_size=page_size,
            review_status=review_status
        )
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"get_pending_indicators failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/admin/review-stats", methods=["GET"])
@login_required
def get_review_stats():
    """
    ---
    tags:
      - General
    summary: "获取审核统计数据（管理员专用）"
    produces:
      - application/json
    security:
      - BearerAuth: []
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        if not _is_admin():
            return jsonify({'code': 0, 'msg': 'admin_required', 'data': None}), 403
        
        service = get_community_service()
        result = service.get_review_stats()
        
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
        
    except Exception as e:
        logger.error(f"get_review_stats failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/admin/indicators/<int:indicator_id>/review", methods=["POST"])
@login_required
def review_indicator(indicator_id: int):
    """
    ---
    tags:
      - Review
    summary: "审核指标（管理员专用）"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
      - name: body
        in: body
        schema:
          type: object
          properties:
            action:
              type: string
            note:
              type: string
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        if not _is_admin():
            return jsonify({'code': 0, 'msg': 'admin_required', 'data': None}), 403
        
        data = request.get_json() or {}
        action = data.get('action', '').strip()
        note = data.get('note', '').strip()
        
        if action not in ('approve', 'reject'):
            return jsonify({'code': 0, 'msg': 'invalid_action', 'data': None}), 400
        
        service = get_community_service()
        success, message = service.review_indicator(
            admin_id=g.user_id,
            indicator_id=indicator_id,
            action=action,
            note=note
        )
        
        if success:
            return jsonify({'code': 1, 'msg': message, 'data': None})
        else:
            return jsonify({'code': 0, 'msg': message, 'data': None}), 400
            
    except Exception as e:
        logger.error(f"review_indicator failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/admin/indicators/<int:indicator_id>/unpublish", methods=["POST"])
@login_required
def unpublish_indicator(indicator_id: int):
    """
    ---
    tags:
      - Unpublish
    summary: "下架指标（管理员专用）"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
      - name: body
        in: body
        schema:
          type: object
          properties:
            note:
              type: string
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        if not _is_admin():
            return jsonify({'code': 0, 'msg': 'admin_required', 'data': None}), 403
        
        data = request.get_json() or {}
        note = data.get('note', '').strip()
        
        service = get_community_service()
        success, message = service.unpublish_indicator(
            admin_id=g.user_id,
            indicator_id=indicator_id,
            note=note
        )
        
        if success:
            return jsonify({'code': 1, 'msg': message, 'data': None})
        else:
            return jsonify({'code': 0, 'msg': message, 'data': None}), 400
            
    except Exception as e:
        logger.error(f"unpublish_indicator failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@community_bp.route("/admin/indicators/<int:indicator_id>", methods=["DELETE"])
@login_required
def admin_delete_indicator(indicator_id: int):
    """
    ---
    tags:
      - Admin
    summary: "删除指标（管理员专用）"
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator Id"
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
      401:
        description: Unauthorized - Invalid or missing token
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        if not _is_admin():
            return jsonify({'code': 0, 'msg': 'admin_required', 'data': None}), 403
        
        service = get_community_service()
        success, message = service.admin_delete_indicator(
            admin_id=g.user_id,
            indicator_id=indicator_id
        )
        
        if success:
            return jsonify({'code': 1, 'msg': message, 'data': None})
        else:
            return jsonify({'code': 0, 'msg': message, 'data': None}), 400
            
    except Exception as e:
        logger.error(f"admin_delete_indicator failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500
