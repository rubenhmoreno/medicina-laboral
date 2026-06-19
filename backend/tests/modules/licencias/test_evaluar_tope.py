from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.licencias.calculo import evaluar_tope
from app.modules.licencias.models import EstadoLicencia, Licencia, OrigenLicencia
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.topes import repository as topes_repo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user


@pytest.mark.asyncio
async def test_excede_tope_calendario_con_licencias_previas(db_session):
    cat = await create_categoria(db_session, CategoriaCreate(codigo="planta", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020, 1, 1), categoria_id=cat.id,
    ))
    user = await create_user(db_session, UsuarioCreate(
        email="rrhh@test.com", password="SuperSecret123!", nombre="RRHH", rol=Rol.RRHH,
    ))
    await topes_repo.set_tope(db_session,
        categoria_id=cat.id, tipo_licencia_id=tipo.id,
        dias_maximos=30, ventana="anio-calendario",
        desde=date(2026, 1, 1), observacion=None,
    )
    # 20 dias ya otorgados en este anio.
    db_session.add(Licencia(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 3, 1), fecha_hasta=date(2026, 3, 20),
        dias_solicitados=20, dias_otorgados=20,
        estado=EstadoLicencia.VALIDADO, origen=OrigenLicencia.RRHH,
        creado_por=user.id,
    ))
    await db_session.flush()

    ev = await evaluar_tope(db_session,
        empleado=emp, tipo_licencia_id=tipo.id, dias_solicitados=15, fecha_ref=date(2026, 6, 1))
    assert ev.tope_aplicable == 30
    assert ev.dias_consumidos_ventana == 20
    assert ev.excede is True
