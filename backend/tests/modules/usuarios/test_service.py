# backend/tests/modules/usuarios/test_service.py
import pytest

from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import authenticate, create_user
from app.shared.exceptions import ConflictError, UnauthorizedError


@pytest.mark.asyncio
async def test_create_and_authenticate(db_session):
    u = await create_user(
        db_session,
        UsuarioCreate(
            email="m@m.com", password="StrongPass123!Q", nombre="M", rol=Rol.MEDICO
        ),
    )
    assert u.id is not None
    again = await authenticate(db_session, "m@m.com", "StrongPass123!Q")
    assert again.id == u.id


@pytest.mark.asyncio
async def test_duplicate_email(db_session):
    p = UsuarioCreate(email="d@d.com", password="StrongPass123!Q", nombre="x", rol=Rol.ADMIN)
    await create_user(db_session, p)
    with pytest.raises(ConflictError):
        await create_user(db_session, p)


@pytest.mark.asyncio
async def test_bad_credentials(db_session):
    with pytest.raises(UnauthorizedError):
        await authenticate(db_session, "nope@nope.com", "xxxxxxxxxxxx")
