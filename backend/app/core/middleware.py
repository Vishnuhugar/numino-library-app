"""
app/core/middleware.py
────────────────────────────────────────────────────────────────────────────
ASGI middleware that:
  • Generates a unique request-id (UUID4) per request.
  • Stores it in the ``request_id_var`` ContextVar so every log statement
    emitted during that request carries the same ID.
  • Echoes the ID in the ``X-Request-Id`` response header so callers can
    correlate their traces.
  • Logs request start (DEBUG) and response finish (INFO) with method, path,
    status code, and elapsed time in milliseconds.
"""
from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_var

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Accept a caller-supplied ID (useful for distributed tracing) or mint one
        req_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        token = request_id_var.set(req_id)

        logger.debug(
            "→ %s %s",
            request.method,
            request.url.path,
        )

        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            logger.exception("Unhandled exception during request")
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            request_id_var.reset(token)

        response.headers["X-Request-Id"] = req_id
        logger.info(
            "← %s %s  %d  %.1f ms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
