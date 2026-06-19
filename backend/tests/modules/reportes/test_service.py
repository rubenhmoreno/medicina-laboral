from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.licencias.models import EstadoLicencia, Licencia, OrigenLicencia
from app.modules.reportes.service import por_area, por_mes
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_por_area_y_por_mes(db_session):
    u = await create_user(db_session, UsuarioCreate(email="u@u.com", password="StrongPass123!Q", nombre="U", rol=Rol.ADMIN))
    cat = await create_categoria(db_session, CategoriaCreate(codigo="p", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020,1,1), categoria_id=cat.id))
    db_session.add(Licencia(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026,3,1), fecha_hasta=date(2026,3,10),
        dias_solicitados=10, dias_otorgados=10,
        estado=EstadoLicencia.VALIDADO, origen=OrigenLicencia.RRHH,
        creado_por=u.id,
    ))
    await db_session.flush()
    a = await por_area(db_session, date(2026,1,1), date(2026,12,31))
    assert a and a[0]["total_dias_otorgados"] == 10
    m = await por_mes(db_session, date(2026,1,1), date(2026,12,31))
    assert any(row["mes"] == 3 and row["total_dias_otorgados"] == 10 for row in m)
