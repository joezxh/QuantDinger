"""Dify workflow executor — streaming and batch modes."""
from __future__ import annotations

import time
from typing import Any, AsyncIterator, Dict

from app.services.dify.dify_client import DifyClient
from app.services.dify.workflow_registry import WorkflowRegistry
from app.database.session import get_session
from app.database.repositories.dify_workflow_repository import DifyWorkflowRepository
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DifyWorkflowExecutor:
    """High-level executor for Dify workflows.

    Handles:
    - Workflow lookup by code
    - Streaming (SSE) and batch (blocking) execution
    - Execution logging
    """

    def __init__(
        self,
        registry: WorkflowRegistry | None = None,
        client: DifyClient | None = None,
    ):
        self.registry = registry or WorkflowRegistry()
        self.client = client or DifyClient()

    # ------------------------------------------------------------------
    # Batch (blocking) execution
    # ------------------------------------------------------------------
    async def run_batch(
        self,
        workflow_code: str,
        inputs: Dict[str, Any],
        user_id: int,
    ) -> Dict[str, Any]:
        """Execute a workflow in blocking mode and return the complete result."""
        workflow = self.registry.get_by_code(workflow_code)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_code}")

        log = self._create_log(workflow.id, user_id, inputs, call_mode="batch")
        started_at = time.time()

        try:
            result = await self.client.chat_blocking(
                endpoint=workflow.endpoint,
                api_key=workflow.api_key,
                inputs=inputs,
                user=str(user_id),
            )
            latency_ms = int((time.time() - started_at) * 1000)
            self._finish_log(log.id, "success", output_data=result, latency_ms=latency_ms)
            return result
        except Exception as exc:
            latency_ms = int((time.time() - started_at) * 1000)
            self._finish_log(
                log.id,
                "failed",
                error_message=str(exc),
                latency_ms=latency_ms,
            )
            raise

    # ------------------------------------------------------------------
    # Streaming execution
    # ------------------------------------------------------------------
    async def run_streaming(
        self,
        workflow_code: str,
        inputs: Dict[str, Any],
        user_id: int,
    ) -> AsyncIterator[str]:
        """Execute a workflow in streaming mode and yield SSE chunks."""
        workflow = self.registry.get_by_code(workflow_code)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_code}")

        log = self._create_log(workflow.id, user_id, inputs, call_mode="streaming")
        started_at = time.time()
        full_output: list[str] = []

        try:
            async for chunk in self.client.chat_stream(
                endpoint=workflow.endpoint,
                api_key=workflow.api_key,
                inputs=inputs,
                user=str(user_id),
            ):
                full_output.append(chunk)
                yield chunk

            latency_ms = int((time.time() - started_at) * 1000)
            self._finish_log(
                log.id,
                "success",
                output_data={"chunks": full_output},
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = int((time.time() - started_at) * 1000)
            self._finish_log(
                log.id,
                "failed",
                error_message=str(exc),
                latency_ms=latency_ms,
            )
            raise

    # ------------------------------------------------------------------
    # Log helpers
    # ------------------------------------------------------------------
    def _create_log(
        self,
        workflow_id: int,
        user_id: int,
        inputs: Dict[str, Any],
        call_mode: str,
    ):
        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                return repo.create_log(
                    workflow_id=workflow_id,
                    user_id=user_id,
                    input_data=inputs,
                    status="running",
                    call_mode=call_mode,
                    started_at=__import__("datetime").datetime.utcnow(),
                )
        except Exception as exc:
            logger.warning(f"Failed to create workflow log: {exc}")
            # Return a dummy object so execution continues
            class _DummyLog:
                id = None
            return _DummyLog()

    def _finish_log(
        self,
        log_id: int | None,
        status: str,
        output_data: Any = None,
        error_message: str | None = None,
        latency_ms: int = 0,
    ):
        if log_id is None:
            return
        try:
            with get_session() as session:
                repo = DifyWorkflowRepository(session)
                repo.update_log_status(
                    log_id=log_id,
                    status=status,
                    output_data=output_data,
                    error_message=error_message,
                    latency_ms=latency_ms,
                    finished_at=__import__("datetime").datetime.utcnow(),
                )
        except Exception as exc:
            logger.warning(f"Failed to finish workflow log {log_id}: {exc}")
