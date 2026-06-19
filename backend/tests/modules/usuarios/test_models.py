import pytest
from sqlalchemy import select

from app.modules.usuarios.models import Rol, Usuario


@pytest.mark.asyncio
async def test_can_create_usuario_with_required_fields(db_session):
    u = Usuario(email="a@b.com", password_hash="h", nombre="A", rol=Rol.ADMIN)
    db_session.add(u)
    await db_session.flush()
    out = (await db_session.execute(select(Usuario).where(Usuario.email == "a@b.com"))).scalar_one()
    assert out.rol == Rol.ADMIN
    assert out.activo is True
