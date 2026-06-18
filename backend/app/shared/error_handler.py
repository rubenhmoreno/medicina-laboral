import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.shared.exceptions import AppError


def _envelope(code: str, message: str, detail: dict[str, Any], request_id: str) -> dict[str, Any]:
    return {
        "error": {"code": code, "message": message, "detail": detail},
        "request_id": request_id,
    }


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        return JSONResponse(
            status_code=exc.http_status,
            content=_envelope(exc.code, exc.message, exc.detail, rid),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex
        # NOTE: stacktrace stays in logs (configured by structlog), never the response.
        return JSONResponse(
            status_code=500,
            content=_envelope("internal_error", "internal server error", {}, rid),
        )
