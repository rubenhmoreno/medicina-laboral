# backend/tests/modules/usuarios/test_router.py
import pytest
from httpx import AsyncClient, ASGITransport

from app.core.deps import get_db
from app.main import create_app
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_login_then_me(db_session):
    await create_user(
        db_session,
        UsuarioCreate(email="z@z.com", password="StrongPass123!Q", nombre="Z", rol=Rol.MEDICO),
    )
    await db_session.flush()

    app = create_app()
    async def _db():
        yield db_session
    app.dependency_overrides[get_db] = _db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        login = await ac.post("/api/auth/login", json={"email": "z@z.com", "password": "StrongPass123!Q"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        me = await ac.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "z@z.com"


@pytest.mark.asyncio
async def test_admin_can_list_users_others_cannot(db_session):
    admin = await create_user(db_session, UsuarioCreate(email="a@a.com", password="StrongPass123!Q", nombre="A", rol=Rol.ADMIN))
    other = await create_user(db_session, UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH))
    await db_session.flush()

    app = create_app()
    async def _db():
        yield db_session
    app.dependency_overrides[get_db] = _db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        a = (await ac.post("/api/auth/login", json={"email": "a@a.com", "password": "StrongPass123!Q"})).json()["access_token"]
        r = (await ac.post("/api/auth/login", json={"email": "r@r.com", "password": "StrongPass123!Q"})).json()["access_token"]
        ok = await ac.get("/api/usuarios", headers={"Authorization": f"Bearer {a}"})
        bad = await ac.get("/api/usuarios", headers={"Authorization": f"Bearer {r}"})
        assert ok.status_code == 200
        assert bad.status_code == 403
