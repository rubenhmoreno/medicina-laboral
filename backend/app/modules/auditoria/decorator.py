from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auditoria import repository as audit_repo


def audited(accion: str, entidad: str) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await fn(*args, **kwargs)
            session: AsyncSession | None = kwargs.get("session") or kwargs.get("db_session")
            request = kwargs.get("request")
            user = kwargs.get("current_user")
            await audit_repo.append(
                session,  # type: ignore[arg-type]
                accion=accion,
                entidad=entidad,
                usuario_id=getattr(user, "id", None),
                entidad_id=getattr(result, "id", None),
                payload={"args": [str(a) for a in args], "kwargs": {k: str(v) for k, v in kwargs.items() if k not in {"session", "db_session", "request", "current_user"}}},
                ip=getattr(getattr(request, "client", None), "host", None),
                user_agent=getattr(request, "headers", {}).get("user-agent") if request else None,
            )
            return result
        return wrapper
    return decorator
