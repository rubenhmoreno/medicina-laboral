from datetime import date

import pytest
from httpx import AsyncClient, ASGITransport

from app.core.deps import get_db
from app.main import create_app
from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_rrhh_no_ve_diagnostico_en_listado(db_session):
    rrhh = await create_user(db_session, UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH))
    cat = await create_categoria(db_session, CategoriaCreate(codigo="p", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020,1,1), categoria_id=cat.id))
    await db_session.flush()

    app = create_app()
    async def _db(): yield db_session
    app.dependency_overrides[get_db] = _db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as ac:
        token = (await ac.post("/api/auth/login", json={"email": "r@r.com", "password": "StrongPass123!Q"})).json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        await ac.post("/api/licencias", headers=h, json={
            "empleado_id": str(emp.id), "tipo_licencia_id": str(tipo.id),
            "fecha_desde": "2026-05-10", "fecha_hasta": "2026-05-15",
            "observaciones": "secret note",
        })
        lst = (await ac.get("/api/licencias", headers=h)).json()
        assert lst[0]["observaciones"] is None
