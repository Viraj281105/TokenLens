"""
TokenLens — API Middleware
===========================
Rate limiting, API key authentication, structured logging, and CORS.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Callable

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("tokenlens.middleware")

# ── API Key Auth ───────────────────────────────────────────────────────

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

_KEY_MASK_RE = re.compile(r"(AIza[A-Za-z0-9_-]{35})")


def _mask_secrets(text: str) -> str:
    """Mask any API keys found in text."""
    return _KEY_MASK_RE.sub("***MASKED***", text)


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    Validate the X-API-Key header against TOKEN_LENS_API_KEY env var.
    If TOKEN_LENS_API_KEY is not set, allow all requests (dev mode).
    """
    expected_key = os.environ.get("TOKEN_LENS_API_KEY")

    if not expected_key:
        # Dev mode: no auth required
        return "dev-mode"

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header",
        )

    if api_key != expected_key:
        logger.warning("Invalid API key attempt: %s", _mask_secrets(api_key[:8] + "..."))
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
        )

    return api_key


# ── Request Logging Middleware ─────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status, and latency."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(elapsed_ms, 2),
                "client_ip": request.client.host if request.client else "unknown",
            },
        )
        return response
