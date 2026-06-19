# backend/app/modules/usuarios/router.py
from fastapi import APIRouter, Depends, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.jwt import decode_token, issue_access, issue_refresh
from app.core.permissions import require_role
from app.core.settings import Settings, get_settings
from app.core.throttle import LoginThrottle
from app.modules.usuarios import repository as repo
from app.modules.usuarios.models import Rol, Usuario
from app.modules.usuarios.schemas import LoginIn, TokenPair, UsuarioCreate, UsuarioOut
from app.modules.usuarios.service import authenticate, create_user
from app.shared.exceptions import UnauthorizedError

router = APIRouter(prefix="/api/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

_throttle = LoginThrottle()


@router.post("/login", response_model=TokenPair)
async def login(
    body: LoginIn,
    request: Request,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    key = f"{body.email}:{request.client.host if request.client else 'na'}"
    if _throttle.is_blocked(key):
        raise UnauthorizedError("too many attempts, try again later")
    try:
        u = await authenticate(session, body.email, body.password)
    except UnauthorizedError:
        _throttle.record_failure(key)
        raise
    _throttle.record_success(key)
    return TokenPair(
        access_token=issue_access(str(u.id), settings),
        refresh_token=issue_refresh(str(u.id), settings),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    refresh_token: str,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        claims = decode_token(refresh_token, settings)
    except JWTError as e:
        raise UnauthorizedError("invalid refresh") from e
    if claims.get("type") != "refresh":
        raise UnauthorizedError("wrong token type")
    u = await repo.get_by_id(session, claims["sub"])
    if u is None or not u.activo:
        raise UnauthorizedError("inactive user")
    return TokenPair(
        access_token=issue_access(str(u.id), settings),
        refresh_token=issue_refresh(str(u.id), settings),
    )


@router.get("/me", response_model=UsuarioOut)
async def me(user: Usuario = Depends(current_user)):
    return user


@users_router.get("", response_model=list[UsuarioOut], dependencies=[Depends(require_role(Rol.ADMIN))])
async def list_users(session: AsyncSession = Depends(get_db)):
    return await repo.list_all(session)


@users_router.post("", response_model=UsuarioOut, status_code=201, dependencies=[Depends(require_role(Rol.ADMIN))])
async def create_endpoint(payload: UsuarioCreate, session: AsyncSession = Depends(get_db)):
    return await create_user(session, payload)
