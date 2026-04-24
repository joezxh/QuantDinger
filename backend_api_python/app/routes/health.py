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
      - Index
    summary: "API 首页"
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
      - Health
    summary: "健康检查"
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
      - Api
    summary: "兼容路径：用于容器健康检查/反代探针等场景。"
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
