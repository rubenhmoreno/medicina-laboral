# backend/tests/core/test_deps.py
import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.deps import current_user, get_db
from app.core.jwt import issue_access
from app.core.permissions import require_role
from app.core.settings import get_settings
from app.modules.usuarios.models import Rol, Usuario
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user
from app.shared.error_handler import install_error_handlers


def build_app(db_session):
    app = FastAPI()
    install_error_handlers(app)

    async def _db_override():
        yield db_session

    app.dependency_overrides[get_db] = _db_override

    @app.get("/me")
    async def me(u: Usuario = Depends(current_user)):
        return {"email": u.email, "rol": u.rol}

    @app.get("/admin-only", dependencies=[Depends(require_role(Rol.ADMIN))])
    async def admin_only():
        return {"ok": True}

    return app


@pytest.mark.asyncio
async def test_me_requires_token(db_session):
    app = build_app(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/me")
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user_with_valid_token(db_session):
    settings = get_settings()
    u = await create_user(
        db_session,
        UsuarioCreate(email="x@y.com", password="StrongPass123!Q", nombre="X", rol=Rol.RRHH),
    )
    await db_session.flush()
    token = issue_access(str(u.id), settings)
    app = build_app(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "x@y.com"


@pytest.mark.asyncio
async def test_admin_only_blocks_non_admin(db_session):
    settings = get_settings()
    u = await create_user(
        db_session,
        UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH),
    )
    await db_session.flush()
    token = issue_access(str(u.id), settings)
    app = build_app(db_session)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        r = await ac.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403
