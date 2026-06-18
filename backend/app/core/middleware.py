import time
import uuid
from collections.abc import Callable
from typing import Any

import structlog
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger("http")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Any:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        start = time.perf_counter()
        structlog.contextvars.bind_contextvars(
            request_id=rid, path=request.url.path, method=request.method
        )
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log.info(
                "request",
                status=getattr(locals().get("response", None), "status_code", 500),
                latency_ms=elapsed_ms,
            )
            structlog.contextvars.clear_contextvars()
        response.headers["x-request-id"] = rid
        return response


def install_request_id_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestIDMiddleware)
