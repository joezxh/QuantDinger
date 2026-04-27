"""Dify API client — thin wrapper around httpx for streaming and blocking calls."""
from __future__ import annotations

import json
import os
from typing import Any, AsyncIterator, Dict

import httpx

from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 120.0


class DifyClient:
    """Low-level Dify API client.

    Supports both **blocking** (batch) and **streaming** (SSE) modes.
    """

    def __init__(self, base_url: str | None = None, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = (base_url or os.getenv("DIFY_API_BASE", "http://localhost:3000")).rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    # ------------------------------------------------------------------
    # Blocking (batch) call
    # ------------------------------------------------------------------
    async def chat_blocking(
        self,
        endpoint: str,
        api_key: str,
        inputs: Dict[str, Any],
        user: str,
        response_mode: str = "blocking",
    ) -> Dict[str, Any]:
        """Send a blocking chat/workflow request and return the full response."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": inputs,
            "user": user,
            "response_mode": response_mode,
        }

        try:
            resp = await self._client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Dify HTTP error {exc.response.status_code}: {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Dify blocking call failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # Streaming (SSE) call
    # ------------------------------------------------------------------
    async def chat_stream(
        self,
        endpoint: str,
        api_key: str,
        inputs: Dict[str, Any],
        user: str,
        response_mode: str = "streaming",
    ) -> AsyncIterator[str]:
        """Send a streaming chat/workflow request and yield SSE chunks."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        payload = {
            "inputs": inputs,
            "user": user,
            "response_mode": response_mode,
        }

        try:
            async with self._client.stream("POST", url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        yield data
        except httpx.HTTPStatusError as exc:
            logger.error(f"Dify streaming HTTP error {exc.response.status_code}: {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Dify streaming call failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def close(self):
        await self._client.aclose()
