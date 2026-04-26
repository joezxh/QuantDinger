"""Dify workflow management and execution API."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.services.dify.workflow_manager import WorkflowManager
from app.services.dify.workflow_executor import DifyWorkflowExecutor
from app.database.session import get_session
from app.database.repositories.dify_workflow_repository import DifyWorkflowRepository
from app.utils.logger import get_logger
from app.utils.auth import login_required

logger = get_logger(__name__)

dify_bp = Blueprint("dify", __name__, url_prefix="/api/dify")

manager = WorkflowManager()
executor = DifyWorkflowExecutor()


# ====================================================================
# Workflow CRUD
# ====================================================================

@dify_bp.route("/workflows", methods=["GET"])
@login_required
def list_workflows():
    """
    ---
    tags:
      - AI/Dify
    summary: "List Dify workflows"
    description: "List all registered Dify workflows with their configuration."
    produces:
      - application/json
    security:
      - BearerAuth: []
    responses:
      200:
        description: Successful response with workflow list
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
      401:
        description: Unauthorized
      500:
        description: Internal Server Error
    """
    try:
        workflows = manager.list_all()
        return jsonify({"success": True, "data": workflows})
    except Exception as exc:
        logger.error(f"list_workflows error: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


@dify_bp.route("/workflows", methods=["POST"])
@login_required
def create_workflow():
    """
    ---
    tags:
      - AI/Dify
    summary: "Create Dify workflow"
    description: "Register a new Dify workflow with code, name, description, and configuration."
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
            - code
            - name
          properties:
            code:
              type: string
              description: "Unique workflow code identifier"
            name:
              type: string
              description: "Workflow display name"
            description:
              type: string
              description: "Workflow description"
            config:
              type: object
              description: "Workflow configuration"
    responses:
      201:
        description: Workflow created successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
      400:
        description: Bad Request - validation error
      401:
        description: Unauthorized
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json(force=True) or {}
        workflow = manager.create(data)
        return jsonify({"success": True, "data": workflow}), 201
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        logger.error(f"create_workflow error: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


@dify_bp.route("/workflows/<code>", methods=["GET"])
@login_required
def get_workflow(code: str):
    """
    ---
    tags:
      - AI/Dify
    summary: "Get workflow detail"
    description: "Retrieve a single Dify workflow's configuration by its code."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: code
        in: path
        type: string
        required: true
        description: "Workflow code identifier"
    responses:
      200:
        description: Successful response with workflow details
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
      401:
        description: Unauthorized
      404:
        description: Workflow not found
      500:
        description: Internal Server Error
    """
    try:
        workflow = manager.get(code)
        if not workflow:
            return jsonify({"success": False, "error": "Workflow not found"}), 404
        return jsonify({"success": True, "data": workflow})
    except Exception as exc:
        logger.error(f"get_workflow error: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


@dify_bp.route("/workflows/<code>", methods=["PUT"])
@login_required
def update_workflow(code: str):
    """
    ---
    tags:
      - AI/Dify
    summary: "Update workflow"
    description: "Update an existing Dify workflow's configuration by its code."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: code
        in: path
        type: string
        required: true
        description: "Workflow code identifier"
      - name: body
        in: body
        required: true
        schema:
          type: object
    responses:
      200:
        description: Workflow updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
      401:
        description: Unauthorized
      404:
        description: Workflow not found
      500:
        description: Internal Server Error
    """
    try:
        data = request.get_json(force=True) or {}
        workflow = manager.update(code, data)
        if not workflow:
            return jsonify({"success": False, "error": "Workflow not found"}), 404
        return jsonify({"success": True, "data": workflow})
    except Exception as exc:
        logger.error(f"update_workflow error: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


@dify_bp.route("/workflows/<code>", methods=["DELETE"])
@login_required
def delete_workflow(code: str):
    """
    ---
    tags:
      - AI/Dify
    summary: "Delete workflow"
    description: "Delete a Dify workflow by its code identifier."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: code
        in: path
        type: string
        required: true
        description: "Workflow code identifier"
    responses:
      200:
        description: Workflow deleted successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
      401:
        description: Unauthorized
      404:
        description: Workflow not found
      500:
        description: Internal Server Error
    """
    try:
        ok = manager.delete(code)
        if not ok:
            return jsonify({"success": False, "error": "Workflow not found"}), 404
        return jsonify({"success": True})
    except Exception as exc:
        logger.error(f"delete_workflow error: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


# ====================================================================
# Execution
# ====================================================================

@dify_bp.route("/workflows/<code>/run", methods=["POST"])
@login_required
def run_workflow(code: str):
    """
    ---
    tags:
      - AI/Dify
    summary: "Execute workflow"
    description: "Execute a Dify workflow by its code with input parameters. Supports batch mode (streaming=false)."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: code
        in: path
        type: string
        required: true
        description: "Workflow code identifier"
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            inputs:
              type: object
              description: "Workflow input parameters"
            streaming:
              type: boolean
              default: false
              description: "Enable streaming mode (not yet implemented)"
    responses:
      200:
        description: Workflow executed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
      400:
        description: Bad Request
      401:
        description: Unauthorized
      501:
        description: Streaming mode not implemented
      500:
        description: Internal Server Error
    """
    from flask import current_app

    try:
        data = request.get_json(force=True) or {}
        inputs = data.get("inputs", {})
        streaming = data.get("streaming", False)
        user_id = getattr(request, "user_id", 0) or getattr(g, "user_id", 0)

        if streaming:
            # Streaming mode — requires async handling at the framework level
            # For Flask (sync), we return an error or fallback to batch.
            # In production this should be served by an ASGI server or
            # a separate streaming endpoint using SSE.
            return jsonify({
                "success": False,
                "error": "Streaming mode requires an async endpoint. Use streaming=false for batch.",
            }), 501

        # Use async-to-sync bridge for batch execution
        import asyncio
        result = asyncio.run(executor.run_batch(code, inputs, user_id))
        return jsonify({"success": True, "data": result})
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        logger.error(f"run_workflow error: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500


# ====================================================================
# Logs
# ====================================================================

@dify_bp.route("/workflows/<code>/logs", methods=["GET"])
@login_required
def get_workflow_logs(code: str):
    """
    ---
    tags:
      - AI/Dify
    summary: "Get workflow logs"
    description: "Retrieve execution logs for a Dify workflow by its code."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: code
        in: path
        type: string
        required: true
        description: "Workflow code identifier"
      - name: limit
        in: query
        type: integer
        required: false
        default: 100
        description: "Max log entries to return"
    responses:
      200:
        description: Successful response with log entries
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
      401:
        description: Unauthorized
      404:
        description: Workflow not found
      500:
        description: Internal Server Error
    """
    try:
        limit = request.args.get("limit", 100, type=int)
        with get_session() as session:
            repo = DifyWorkflowRepository(session)
            wf = repo.get_by_code(code)
            if not wf:
                return jsonify({"success": False, "error": "Workflow not found"}), 404

            logs = repo.get_logs_by_workflow(wf.id, limit=limit)
            data = [
                {
                    "id": log.id,
                    "status": log.status,
                    "call_mode": log.call_mode,
                    "tokens_used": log.tokens_used,
                    "latency_ms": log.latency_ms,
                    "error_message": log.error_message,
                    "started_at": log.started_at.isoformat() if log.started_at else None,
                    "finished_at": log.finished_at.isoformat() if log.finished_at else None,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ]
            return jsonify({"success": True, "data": data})
    except Exception as exc:
        logger.error(f"get_workflow_logs error: {exc}")
        return jsonify({"success": False, "error": str(exc)}), 500
