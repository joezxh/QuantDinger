from flask import Blueprint, request, jsonify, g
from app.utils.auth import login_required, admin_required
from app.utils.db import get_db_connection
from app.utils.crypto import crypto_utils
from app.utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)
llm_bp = Blueprint('llm', __name__)

# ==================== Provider Management ====================

@llm_bp.route('/provider/list', methods=['GET'])
@login_required
@admin_required
def list_providers():
    """
    ---
    tags:
      - List
    summary: "List Providers"
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
      403:
        description: Forbidden - Admin access required
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute("SELECT * FROM qd_llm_provider ORDER BY id ASC")
            rows = cur.fetchall()
            cur.close()
            return jsonify({'code': 1, 'msg': 'success', 'data': rows})
    except Exception as e:
        logger.error(f"list_providers failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

@llm_bp.route('/provider/create', methods=['POST'])
@login_required
@admin_required
def create_provider():
    """
    ---
    tags:
      - General
    summary: "Create Provider"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            api_type:
              type: string
            base_url:
              type: string
            status:
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
      403:
        description: Forbidden - Admin access required
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json()
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                """
                INSERT INTO qd_llm_provider (name, code, api_type, base_url, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (data['name'], data['code'], data.get('api_type', 'openai'), data.get('base_url', ''), data.get('status', 1))
            )
            db.commit()
            cur.close()
            return jsonify({'code': 1, 'msg': 'Provider created'})
    except Exception as e:
        logger.error(f"create_provider failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

@llm_bp.route('/provider/update', methods=['PUT'])
@login_required
@admin_required
def update_provider():
    """
    ---
    tags:
      - General
    summary: "Update Provider"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            id:
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
      403:
        description: Forbidden - Admin access required
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json()
        provider_id = data.get('id')
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                """
                UPDATE qd_llm_provider 
                SET name = ?, code = ?, api_type = ?, base_url = ?, status = ?, updated_at = NOW()
                WHERE id = ?
                """,
                (data['name'], data['code'], data['api_type'], data['base_url'], data['status'], provider_id)
            )
            db.commit()
            cur.close()
            return jsonify({'code': 1, 'msg': 'Provider updated'})
    except Exception as e:
        logger.error(f"update_provider failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

# ==================== API Key Management ====================

@llm_bp.route('/key/list', methods=['GET'])
@login_required
def list_keys():
    """
    ---
    tags:
      - List
    summary: "List Keys"
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
        user_id = g.user_id
        is_admin = (g.user.get('role') == 'admin')
        
        with get_db_connection() as db:
            cur = db.cursor()
            if is_admin:
                cur.execute(
                    """
                    SELECT k.*, p.name as provider_name 
                    FROM qd_llm_api_key k
                    JOIN qd_llm_provider p ON k.provider_id = p.id
                    ORDER BY k.id DESC
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT k.*, p.name as provider_name 
                    FROM qd_llm_api_key k
                    JOIN qd_llm_provider p ON k.provider_id = p.id
                    WHERE k.owner_id = ? OR k.is_public = 1
                    ORDER BY k.id DESC
                    """,
                    (user_id,)
                )
            rows = cur.fetchall()
            cur.close()
            
            # Mask API keys for security
            for row in rows:
                if 'api_key_enc' in row:
                    del row['api_key_enc']
                row['key_masked'] = "****" # In a real UI we might show prefix/suffix
                
            return jsonify({'code': 1, 'msg': 'success', 'data': rows})
    except Exception as e:
        logger.error(f"list_keys failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

@llm_bp.route('/key/create', methods=['POST'])
@login_required
def create_key():
    """
    ---
    tags:
      - General
    summary: "Create Key"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            is_public:
              type: string
            weight:
              type: string
            status:
              type: string
            remark:
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
        data = request.get_json()
        user_id = g.user_id
        is_admin = (g.user.get('role') == 'admin')
        
        # Only admin can create public keys
        is_public = 1 if (is_admin and data.get('is_public')) else 0
        
        api_key_enc = crypto_utils.encrypt(data['api_key'])
        
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                """
                INSERT INTO qd_llm_api_key (provider_id, api_key_enc, owner_id, is_public, weight, status, remark)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (data['provider_id'], api_key_enc, user_id, is_public, data.get('weight', 10), data.get('status', 1), data.get('remark', ''))
            )
            db.commit()
            cur.close()
            return jsonify({'code': 1, 'msg': 'API Key added'})
    except Exception as e:
        logger.error(f"create_key failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

@llm_bp.route('/key/update', methods=['PUT'])
@login_required
def update_key():
    """
    ---
    tags:
      - General
    summary: "Update Key"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            id:
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
        data = request.get_json()
        key_id = data.get('id')
        user_id = g.user_id
        is_admin = (g.user.get('role') == 'admin')
        
        with get_db_connection() as db:
            cur = db.cursor()
            # Verify ownership
            cur.execute("SELECT owner_id FROM qd_llm_api_key WHERE id = ?", (key_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({'code': 0, 'msg': 'Key not found'}), 404
            
            if not is_admin and row['owner_id'] != user_id:
                return jsonify({'code': 0, 'msg': 'Permission denied'}), 403
            
            update_fields = []
            params = []
            
            if 'weight' in data:
                update_fields.append("weight = ?")
                params.append(data['weight'])
            if 'status' in data:
                update_fields.append("status = ?")
                params.append(data['status'])
            if 'remark' in data:
                update_fields.append("remark = ?")
                params.append(data['remark'])
            if 'api_key' in data and data['api_key']:
                update_fields.append("api_key_enc = ?")
                params.append(crypto_utils.encrypt(data['api_key']))
            if is_admin and 'is_public' in data:
                update_fields.append("is_public = ?")
                params.append(1 if data['is_public'] else 0)
                
            if not update_fields:
                return jsonify({'code': 0, 'msg': 'No fields to update'})
            
            params.append(key_id)
            cur.execute(
                f"UPDATE qd_llm_api_key SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = ?",
                tuple(params)
            )
            db.commit()
            cur.close()
            return jsonify({'code': 1, 'msg': 'API Key updated'})
    except Exception as e:
        logger.error(f"update_key failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

# ==================== Model Management ====================

@llm_bp.route('/model/list', methods=['GET'])
@login_required
def list_models():
    """
    ---
    tags:
      - List
    summary: "List Models"
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
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                """
                SELECT m.*, p.name as provider_name 
                FROM qd_llm_model m
                JOIN qd_llm_provider p ON m.provider_id = p.id
                ORDER BY m.id DESC
                """
            )
            rows = cur.fetchall()
            cur.close()
            return jsonify({'code': 1, 'msg': 'success', 'data': rows})
    except Exception as e:
        logger.error(f"list_models failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

@llm_bp.route('/model/create', methods=['POST'])
@login_required
@admin_required
def create_model():
    """
    ---
    tags:
      - General
    summary: "Create Model"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            lb_strategy:
              type: string
            retries:
              type: string
            timeout:
              type: string
            status:
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
      403:
        description: Forbidden - Admin access required
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json()
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                """
                INSERT INTO qd_llm_model (provider_id, model_name, lb_strategy, retries, timeout, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (data['provider_id'], data['model_name'], data.get('lb_strategy', 'weighted_round_robin'), 
                 data.get('retries', 3), data.get('timeout', 120), data.get('status', 1))
            )
            db.commit()
            cur.close()
            return jsonify({'code': 1, 'msg': 'Model created'})
    except Exception as e:
        logger.error(f"create_model failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

@llm_bp.route('/model/update', methods=['PUT'])
@login_required
@admin_required
def update_model():
    """
    ---
    tags:
      - General
    summary: "Update Model"
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            id:
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
      403:
        description: Forbidden - Admin access required
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json()
        model_id = data.get('id')
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                """
                UPDATE qd_llm_model 
                SET provider_id = ?, model_name = ?, lb_strategy = ?, retries = ?, timeout = ?, status = ?, updated_at = NOW()
                WHERE id = ?
                """,
                (data['provider_id'], data['model_name'], data['lb_strategy'], 
                 data['retries'], data['timeout'], data['status'], model_id)
            )
            db.commit()
            cur.close()
            return jsonify({'code': 1, 'msg': 'Model updated'})
    except Exception as e:
        logger.error(f"update_model failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500

# ==================== Monitoring ====================

@llm_bp.route('/monitor/stats', methods=['GET'])
@login_required
@admin_required
def get_stats():
    """
    ---
    tags:
      - General
    summary: "Get Stats"
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
      403:
        description: Forbidden - Admin access required
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    try:
        # Get last 24h stats
        with get_db_connection() as db:
            cur = db.cursor()
            cur.execute(
                """
                SELECT 
                    m.model_name, 
                    p.name as provider_name,
                    COUNT(*) as total_calls,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as success_rate
                FROM qd_llm_call_log l
                JOIN qd_llm_model m ON l.model_id = m.id
                JOIN qd_llm_provider p ON m.provider_id = p.id
                WHERE l.created_at > NOW() - INTERVAL '24 hours'
                GROUP BY m.model_name, p.name
                """
            )
            rows = cur.fetchall()
            cur.close()
            return jsonify({'code': 1, 'msg': 'success', 'data': rows})
    except Exception as e:
        logger.error(f"get_stats failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500
