from typing import Any


class AppError(Exception):
    http_status: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "", detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class ValidationError(AppError):
    http_status = 422
    code = "validation"


class NotFoundError(AppError):
    http_status = 404
    code = "not_found"


class ConflictError(AppError):
    http_status = 409
    code = "conflict"


class ForbiddenError(AppError):
    http_status = 403
    code = "forbidden"


class UnauthorizedError(AppError):
    http_status = 401
    code = "unauthorized"


class InvalidStateTransition(ConflictError):
    code = "invalid_transition"
