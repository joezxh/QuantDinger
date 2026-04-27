from flask import Blueprint, request, jsonify, g
from app.utils.auth import login_required, admin_required
from app.utils.crypto import crypto_utils
from app.utils.logger import get_logger
from app.database.session import get_session
from app.database.repositories.llm_repository import LLmRepository
from datetime import datetime

logger = get_logger(__name__)
llm_bp = Blueprint('llm', __name__)


def _get_repo():
    """Get LLM repository bound to current session."""
    # Session is managed at route level via get_session()
    # We return a factory-created repo; session is injected by caller
    return None  # Placeholder - actual repo created per-request


# ==================== Provider Management ====================

@llm_bp.route('/provider/list', methods=['GET'])
@login_required
@admin_required
def list_providers():
    """
    ---
    tags:
      - System/LLM
    summary: "List LLM providers"
    description: "Admin only. List all configured LLM providers with their status and configuration."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with provider list
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
              type: array
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Admin access required
      500:
        description: Internal server error
    """
    try:
        with get_session() as session:
            repo = LLmRepository(session)
            providers = repo.list_providers()
            result = [
                {
                    "id": p.id, "name": p.name, "code": p.code,
                    "api_type": p.api_type, "base_url": p.base_url,
                    "status": p.status, "config": p.config,
                    "created_at": str(p.created_at) if p.created_at else None,
                    "updated_at": str(p.updated_at) if p.updated_at else None,
                }
                for p in providers
            ]
            return jsonify({'code': 1, 'msg': 'success', 'data': result})
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
      - System/LLM
    summary: "Create LLM provider"
    description: "Admin only. Create a new LLM provider configuration."
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
            - name
            - code
          properties:
            name:
              type: string
              description: "Provider display name"
            code:
              type: string
              description: "Unique provider code identifier"
            api_type:
              type: string
              default: openai
              description: "API type (openai, etc.)"
            base_url:
              type: string
              description: "API base URL"
            status:
              type: integer
              default: 1
              description: "Provider status (1=active)"
    responses:
      200:
        description: Provider created successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: Provider created
      400:
        description: Bad Request - missing or duplicate code
      401:
        description: Unauthorized
      403:
        description: Forbidden - Admin access required
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()

        # Validate required fields
        name = data.get('name')
        code = data.get('code')

        if not name:
            return jsonify({'code': 0, 'msg': 'Name is required'}), 400
        if not code:
            return jsonify({'code': 0, 'msg': 'Code is required'}), 400

        with get_session() as session:
            repo = LLmRepository(session)
            # Check if code already exists
            existing = repo.get_provider_by_code(code)
            if existing:
                return jsonify({'code': 0, 'msg': 'Code already exists'}), 400

            repo.create_provider(
                name=name,
                code=code,
                api_type=data.get('api_type', 'openai'),
                base_url=data.get('base_url', ''),
                status=data.get('status', 1),
            )
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
      - System/LLM
    summary: "Update LLM provider"
    description: "Admin only. Update an existing LLM provider configuration."
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
            - id
          properties:
            id:
              type: integer
              description: "Provider ID"
            name:
              type: string
              description: "Provider display name"
            code:
              type: string
              description: "Unique provider code"
            api_type:
              type: string
              description: "API type"
            base_url:
              type: string
              description: "API base URL"
            status:
              type: integer
              description: "Provider status"
    responses:
      200:
        description: Provider updated successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: Provider updated
      400:
        description: Bad Request
      401:
        description: Unauthorized
      403:
        description: Forbidden - Admin access required
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        provider_id = data.get('id')

        # Validate required fields
        name = data.get('name')
        code = data.get('code')

        if not name:
            return jsonify({'code': 0, 'msg': 'Name is required'}), 400
        if not code:
            return jsonify({'code': 0, 'msg': 'Code is required'}), 400

        with get_session() as session:
            repo = LLmRepository(session)
            # Check if code already exists for other providers
            existing = repo.get_provider_by_code(code)
            if existing and existing.id != provider_id:
                return jsonify({'code': 0, 'msg': 'Code already exists'}), 400

            repo.update_provider(
                provider_id,
                name=name,
                code=code,
                api_type=data.get('api_type'),
                base_url=data.get('base_url'),
                status=data.get('status'),
            )
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
      - System/LLM
    summary: "List LLM API keys"
    description: "Retrieve the current user's LLM API keys with masked sensitive fields."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with key list
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
              type: array
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        user_id = g.user_id
        is_admin = (g.user_role == 'admin')

        with get_session() as session:
            repo = LLmRepository(session)
            rows = repo.list_keys(admin=is_admin, user_id=user_id)

            # Mask API keys for security
            for row in rows:
                if 'api_key_enc' in row:
                    del row['api_key_enc']
                # Serialize datetime fields
                for dt_field in ('created_at', 'updated_at', 'last_used_at'):
                    if dt_field in row and row[dt_field] is not None:
                        row[dt_field] = str(row[dt_field])

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
      - System/LLM
    summary: "Create LLM API key"
    description: "Add a new LLM API key for the current user or as a public key (admin only)."
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
            - provider_id
            - api_key
          properties:
            provider_id:
              type: integer
              description: "Provider ID"
            api_key:
              type: string
              description: "API key value"
            is_public:
              type: boolean
              description: "Whether the key is public (admin only)"
            weight:
              type: integer
              default: 10
              description: "Load balancing weight"
            status:
              type: integer
              default: 1
              description: "Key status (1=active)"
            name:
              type: string
              description: "Key display name or remark"
    responses:
      200:
        description: API key created successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: API Key added
      400:
        description: Bad Request
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        user_id = g.user_id
        is_admin = (g.user_role == 'admin')

        # Only admin can create public keys
        is_public = 1 if (is_admin and data.get('is_public')) else 0

        api_key_enc = crypto_utils.encrypt(data['api_key'])

        with get_session() as session:
            repo = LLmRepository(session)
            repo.create_key(
                provider_id=data['provider_id'],
                api_key_enc=api_key_enc,
                owner_id=user_id,
                is_public=is_public,
                weight=data.get('weight', 10),
                status=data.get('status', 1),
                name=data.get('name') or data.get('remark', ''),
            )
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
      - System/LLM
    summary: "Update LLM API key"
    description: "Update an existing LLM API key's weight, status, name, or key value."
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
            - id
          properties:
            id:
              type: integer
              description: "Key ID"
            weight:
              type: integer
              description: "Load balancing weight"
            status:
              type: integer
              description: "Key status"
            name:
              type: string
              description: "Key display name"
            api_key:
              type: string
              description: "New API key value (optional)"
    responses:
      200:
        description: API key updated successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: API Key updated
      400:
        description: Bad Request
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: Key not found
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        key_id = data.get('id')
        user_id = g.user_id
        is_admin = (g.user_role == 'admin')

        with get_session() as session:
            repo = LLmRepository(session)
            key = repo.get_key_by_id(key_id)
            if not key:
                return jsonify({'code': 0, 'msg': 'Key not found'}), 404

            if not is_admin and key.owner_id != user_id:
                return jsonify({'code': 0, 'msg': 'Permission denied'}), 403

            update_fields = {}
            if 'weight' in data:
                update_fields['weight'] = data['weight']
            if 'status' in data:
                update_fields['status'] = data['status']
            if 'name' in data:
                update_fields['name'] = data['name']
            elif 'remark' in data:
                update_fields['name'] = data['remark']
            if 'api_key' in data and data['api_key']:
                update_fields['api_key_enc'] = crypto_utils.encrypt(data['api_key'])
            if is_admin and 'is_public' in data:
                update_fields['is_public'] = 1 if data['is_public'] else 0

            if not update_fields:
                return jsonify({'code': 0, 'msg': 'No fields to update'})

            repo.update_key(key_id, **update_fields)
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
      - System/LLM
    summary: "List LLM models"
    description: "Retrieve the list of configured LLM models with their load balancing strategy and status."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with model list
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
              type: array
      401:
        description: Unauthorized
      500:
        description: Internal server error
    """
    try:
        with get_session() as session:
            repo = LLmRepository(session)
            rows = repo.list_models()
            # Serialize datetime fields
            for row in rows:
                for dt_field in ('created_at', 'updated_at'):
                    if dt_field in row and row[dt_field] is not None:
                        row[dt_field] = str(row[dt_field])
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
      - System/LLM
    summary: "Create LLM model"
    description: "Admin only. Register a new LLM model with a provider and load balancing configuration."
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
            - provider_id
            - model_name
          properties:
            provider_id:
              type: integer
              description: "Provider ID"
            model_name:
              type: string
              description: "Model name identifier"
            lb_strategy:
              type: string
              default: weighted_round_robin
              description: "Load balancing strategy"
            retries:
              type: integer
              default: 3
              description: "Max retry count"
            timeout:
              type: integer
              default: 120
              description: "Request timeout in seconds"
            status:
              type: integer
              default: 1
              description: "Model status (1=active)"
    responses:
      200:
        description: Model created successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: Model created
      400:
        description: Bad Request
      401:
        description: Unauthorized
      403:
        description: Forbidden - Admin access required
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        with get_session() as session:
            repo = LLmRepository(session)
            repo.create_model(
                provider_id=data['provider_id'],
                model_name=data['model_name'],
                display_name=data.get('display_name'),
                lb_strategy=data.get('lb_strategy', 'weighted_round_robin'),
                retries=data.get('retries', 3),
                timeout=data.get('timeout', 120),
                status=data.get('status', 1),
            )
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
      - System/LLM
    summary: "Update LLM model"
    description: "Admin only. Update an existing LLM model configuration."
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
            - id
          properties:
            id:
              type: integer
              description: "Model ID"
            provider_id:
              type: integer
              description: "Provider ID"
            model_name:
              type: string
              description: "Model name"
            lb_strategy:
              type: string
              description: "Load balancing strategy"
            retries:
              type: integer
              description: "Max retry count"
            timeout:
              type: integer
              description: "Request timeout in seconds"
            status:
              type: integer
              description: "Model status"
    responses:
      200:
        description: Model updated successfully
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: Model updated
      400:
        description: Bad Request
      401:
        description: Unauthorized
      403:
        description: Forbidden - Admin access required
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        model_id = data.get('id')
        with get_session() as session:
            repo = LLmRepository(session)
            model = repo.get_model_by_id(model_id)
            if not model:
                return jsonify({'code': 0, 'msg': 'Model not found'}), 404
            update_fields = {}
            if 'provider_id' in data:
                update_fields['provider_id'] = data['provider_id']
            if 'model_name' in data:
                update_fields['model_name'] = data['model_name']
            if 'display_name' in data:
                update_fields['display_name'] = data['display_name']
            if 'lb_strategy' in data:
                update_fields['lb_strategy'] = data['lb_strategy']
            if 'retries' in data:
                update_fields['retries'] = data['retries']
            if 'timeout' in data:
                update_fields['timeout'] = data['timeout']
            if 'status' in data:
                update_fields['status'] = data['status']

            if not update_fields:
                return jsonify({'code': 0, 'msg': 'No fields to update'}), 400

            repo.update_model(model_id, **update_fields)
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
      - System/LLM
    summary: "Get LLM monitor stats"
    description: "Admin only. Retrieve LLM usage monitoring statistics."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with monitor stats
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
              type: array
      401:
        description: Unauthorized
      403:
        description: Forbidden - Admin access required
      500:
        description: Internal server error
    """
    try:
        with get_session() as session:
            repo = LLmRepository(session)
            rows = repo.get_monitor_stats()
            return jsonify({'code': 1, 'msg': 'success', 'data': rows})
    except Exception as e:
        logger.error(f"get_stats failed: {e}")
        return jsonify({'code': 0, 'msg': str(e)}), 500
