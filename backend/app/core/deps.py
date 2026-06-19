# backend/app/core/deps.py
from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import Depends, Header
from jose import JWTError  # type: ignore[import-untyped]
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import sessionmaker_factory
from app.core.jwt import decode_token
from app.core.settings import Settings, get_settings
from app.modules.usuarios import repository as users_repo
from app.modules.usuarios.models import Usuario
from app.shared.exceptions import UnauthorizedError


@lru_cache
def _factory(dsn: str) -> async_sessionmaker[AsyncSession]:
    return sessionmaker_factory(dsn)


async def get_db(
    settings: Settings = Depends(get_settings),
) -> AsyncGenerator[AsyncSession, None]:
    f = _factory(settings.db_dsn)
    async with f() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def current_user(
    authorization: str = Header(default=""),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db),
) -> Usuario:
    if not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        claims = decode_token(token, settings)
    except JWTError as e:
        raise UnauthorizedError("invalid token") from e
    if claims.get("type") != "access":
        raise UnauthorizedError("wrong token type")
    user = await users_repo.get_by_id(session, claims["sub"])
    if user is None or not user.activo:
        raise UnauthorizedError("inactive user")
    return user
