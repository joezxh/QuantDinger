"""
健康检查路由
"""
from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)


@health_bp.route('/', methods=['GET'])
def index():
    """
    ---
    tags:
      - System/Health
    summary: "API index / homepage"
    description: "Returns basic API information including name, version, and status."
    produces:
      - application/json
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
        description: Bad Request
      500:
        description: Internal Server Error
    """
    return jsonify({
        'name': 'QuantDinger Python API',
        'version': '2.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    ---
    tags:
      - System/Health
    summary: "Health check endpoint"
    description: "Returns service health status and current timestamp."
    produces:
      - application/json
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
        description: Bad Request
      500:
        description: Internal Server Error
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@health_bp.route('/api/health', methods=['GET'])
def api_health_check():
    """
    ---
    tags:
      - System/Health
    summary: "Health check (compatible path)"
    description: "Compatibility endpoint for container health checks and reverse proxy probes."
    produces:
      - application/json
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
        description: Bad Request
      500:
        description: Internal Server Error
    """
    return health_check()
