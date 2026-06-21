"""
middleware/audit_middleware.py

Request-level audit middleware.

Logs every inbound HTTP request with method, path, and response status.
This is a lightweight supplement to the in-handler audit_service calls —
it catches cases like 404s and 422s that don't reach business logic.

Usage:
    app.add_middleware(AuditRequestMiddleware)
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuditRequestMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request at INFO level.
    Skips health-check endpoint to avoid noise.

    In production, swap `print` for a structured logger (e.g., structlog).
    """

    SKIP_PATHS = {"/health", "/api/docs", "/api/redoc", "/api/openapi.json"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Structured log line — replace with logging.getLogger(__name__).info(...)
        print(
            f"[REQUEST] {request.method} {request.url.path} "
            f"-> {response.status_code} ({elapsed_ms:.1f}ms) "
            f"IP={request.client.host if request.client else '-'}"
        )

        return response
