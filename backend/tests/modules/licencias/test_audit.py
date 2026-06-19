from datetime import date

import pytest
from sqlalchemy import select

from app.modules.auditoria.models import Auditoria
from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.licencias.schemas import LicenciaCreate
from app.modules.licencias.service import crear_licencia, enviar
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_state_change_genera_audit(db_session):
    rrhh = await create_user(db_session, UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH))
    cat = await create_categoria(db_session, CategoriaCreate(codigo="p", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020,1,1), categoria_id=cat.id))
    await db_session.flush()
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026,5,10), fecha_hasta=date(2026,5,15),
    ), actor=rrhh)
    await enviar(db_session, lic_id=lic.id, actor=rrhh)
    rows = (await db_session.execute(select(Auditoria))).scalars().all()
    assert any(a.accion == "state_change" and a.entidad == "licencia" for a in rows)
