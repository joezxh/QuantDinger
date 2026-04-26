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
      - Community/Indicators
    summary: "Get market indicator list"
    description: "Retrieve paginated list of community indicators with optional keyword search, pricing filter, and sort."
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
        default: 12
        description: "Items per page, max 50"
      - name: keyword
        in: query
        type: string
        required: false
        description: "Search keyword"
      - name: pricing_type
        in: query
        type: string
        required: false
        description: "Pricing type filter (free/paid)"
      - name: sort_by
        in: query
        type: string
        required: false
        default: newest
        description: "Sort field (newest, popular, rating)"
    responses:
      200:
        description: Successful response with indicator list
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
      - Community/Indicators
    summary: "Get indicator detail"
    description: "Retrieve detailed information about a specific community indicator by ID."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator ID"
    responses:
      200:
        description: Successful response with indicator details
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
      404:
        description: Indicator not found
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
      - Community/Purchases
    summary: "Purchase indicator"
    description: "Purchase a community indicator from the indicator marketplace."
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
        description: "Indicator ID"
    responses:
      200:
        description: Indicator purchased successfully
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
        description: Bad Request - e.g. insufficient credits
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
      - Community/Purchases
    summary: "Sync purchased indicator code"
    description: "Sync the latest version of a purchased indicator's code to the user's local indicator library."
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
        description: "Indicator ID"
    responses:
      200:
        description: Indicator synced successfully
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
      403:
        description: Not purchased this indicator
      404:
        description: Indicator not found or unpublished
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
      - Community/Purchases
    summary: "Get my purchased indicators"
    description: "Return the current user's purchased indicator list with pagination."
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
        description: "Items per page, max 50"
    responses:
      200:
        description: Successful response with purchased indicator list
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
      - Community/Comments
    summary: "Get indicator comments"
    description: "Retrieve paginated comments for a specific community indicator."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator ID"
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
        description: "Items per page, max 50"
    responses:
      200:
        description: Successful response with comment list
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
      - Community/Comments
    summary: "Add comment"
    description: "Add a rating and comment to a community indicator."
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
        description: "Indicator ID"
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            rating:
              type: integer
              default: 5
              description: "Rating score (1-5)"
            content:
              type: string
              description: "Comment text content"
    responses:
      200:
        description: Comment added successfully
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
      - Community/Comments
    summary: "Update comment"
    description: "Update the current user's own comment on an indicator (rating and/or content)."
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
        description: "Indicator ID"
      - name: comment_id
        in: path
        type: integer
        required: true
        description: "Comment ID"
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            rating:
              type: integer
              description: "Updated rating score (1-5)"
            content:
              type: string
              description: "Updated comment text"
    responses:
      200:
        description: Comment updated successfully
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
      - Community/Comments
    summary: "Get my comment"
    description: "Retrieve the current user's comment on a specific indicator (for editing purposes)."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator ID"
    responses:
      200:
        description: Successful response with user's comment
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
      - Community/Indicators
    summary: "Get indicator performance stats"
    description: "Retrieve live trading performance statistics for a specific community indicator."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator ID"
    responses:
      200:
        description: Successful response with performance stats
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
      - Community/Admin
    summary: "Get pending review indicators"
    description: "Admin only. Retrieve paginated list of indicators pending review with status filter."
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
      - name: review_status
        in: query
        type: string
        required: false
        default: pending
        description: "Review status filter (pending, approved, rejected)"
    responses:
      200:
        description: Successful response with pending indicator list
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
      403:
        description: Forbidden - Admin access required
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
      - Community/Admin
    summary: "Get review statistics"
    description: "Admin only. Retrieve aggregate review statistics for the indicator marketplace."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with review stats
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
      403:
        description: Forbidden - Admin access required
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
      - Community/Admin
    summary: "Review indicator"
    description: "Admin only. Approve or reject a community indicator with an optional review note."
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
        description: "Indicator ID"
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            action:
              type: string
              description: "Review action (approve/reject)"
            note:
              type: string
              description: "Optional review note"
    responses:
      200:
        description: Indicator reviewed successfully
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
      403:
        description: Forbidden - Admin access required
      400:
        description: Bad Request - invalid action
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
      - Community/Admin
    summary: "Unpublish indicator"
    description: "Admin only. Remove a community indicator from the marketplace (unpublish)."
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
        description: "Indicator ID"
      - name: body
        in: body
        schema:
          type: object
          properties:
            note:
              type: string
              description: "Reason for unpublishing"
    responses:
      200:
        description: Indicator unpublished successfully
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
      403:
        description: Forbidden - Admin access required
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
      - Community/Admin
    summary: "Delete indicator"
    description: "Admin only. Permanently delete a community indicator by ID."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: indicator_id
        in: path
        type: integer
        required: true
        description: "Indicator ID"
    responses:
      200:
        description: Indicator deleted successfully
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
      403:
        description: Forbidden - Admin access required
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
