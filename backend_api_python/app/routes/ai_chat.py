"""
AI chat API routes (optional).
Currently kept as a minimal compatibility layer for legacy frontend calls.
"""

from flask import Blueprint, request, jsonify

from app.utils.logger import get_logger

logger = get_logger(__name__)

ai_chat_bp = Blueprint('ai_chat', __name__)


@ai_chat_bp.route('/chat/message', methods=['POST'])
def chat_message():
    """
    ---
    tags:
      - Chat
    summary: "Minimal placeholder for legacy chat."
    produces:
      - application/json
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        schema:
          type: object
          properties:
            message:
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
      400:
        description: Bad Request
      500:
        description: Internal Server Error
    """
    data = request.get_json() or {}
    msg = (data.get('message') or '').strip()
    if not msg:
        return jsonify({'code': 0, 'msg': 'Missing message', 'data': None}), 400
    return jsonify({
        'code': 1,
        'msg': 'success',
        'data': {
            'reply': 'Chat API is not implemented yet in local-only mode.',
            'echo': msg
        }
    })


@ai_chat_bp.route('/chat/history', methods=['GET'])
def get_chat_history():
    """
    ---
    tags:
      - General
    summary: "Return empty history (compatibility stub)."
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
    return jsonify({'code': 1, 'msg': 'success', 'data': []})


@ai_chat_bp.route('/chat/history/save', methods=['POST'])
def save_chat_history():
    """
    ---
    tags:
      - Save
    summary: "No-op save (compatibility stub)."
    produces:
      - application/json
    consumes:
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
    return jsonify({'code': 1, 'msg': 'success', 'data': None})


