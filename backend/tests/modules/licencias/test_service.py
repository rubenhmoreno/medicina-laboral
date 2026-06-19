from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.modules.licencias.models import EstadoLicencia
from app.modules.licencias.schemas import LicenciaCreate, RechazarIn, ValidarIn
from app.modules.licencias.service import crear_licencia, enviar, rechazar, validar
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.topes import repository as topes_repo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user
from app.shared.exceptions import InvalidStateTransition


async def _setup(db_session):
    rrhh = await create_user(db_session, UsuarioCreate(email="r@r.com", password="StrongPass123!Q", nombre="R", rol=Rol.RRHH))
    medico = await create_user(db_session, UsuarioCreate(email="m@m.com", password="StrongPass123!Q", nombre="M", rol=Rol.MEDICO))
    cat = await create_categoria(db_session, CategoriaCreate(codigo="planta", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="EC"))
    await db_session.flush()
    emp = await create_empleado(db_session, EmpleadoCreate(
        legajo="L1", cuil="20111111119", nombre="A", apellido="B",
        fecha_ingreso=date(2020, 1, 1), categoria_id=cat.id,
    ))
    await topes_repo.set_tope(db_session,
        categoria_id=cat.id, tipo_licencia_id=tipo.id,
        dias_maximos=30, ventana="anio-calendario",
        desde=date(2026, 1, 1), observacion=None,
    )
    return rrhh, medico, cat, tipo, emp


@pytest.mark.asyncio
async def test_crear_calcula_dias_y_estado_borrador(db_session):
    rrhh, _, _, tipo, emp = await _setup(db_session)
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 5, 10), fecha_hasta=date(2026, 5, 15),
    ), actor=rrhh)
    assert lic.dias_solicitados == 6
    assert lic.estado == EstadoLicencia.BORRADOR
    assert lic.origen.value == "rrhh"


@pytest.mark.asyncio
async def test_enviar_y_validar_flow(db_session):
    rrhh, medico, _, tipo, emp = await _setup(db_session)
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 5, 10), fecha_hasta=date(2026, 5, 15),
    ), actor=rrhh)
    lic = await enviar(db_session, lic_id=lic.id, actor=rrhh)
    assert lic.estado == EstadoLicencia.ENVIADO
    lic = await validar(db_session, lic_id=lic.id, payload=ValidarIn(dias_otorgados=6), actor=medico)
    assert lic.estado == EstadoLicencia.VALIDADO
    assert lic.dias_otorgados == 6
    assert lic.validado_por == medico.id


@pytest.mark.asyncio
async def test_rechazar_requiere_motivo(db_session):
    rrhh, medico, _, tipo, emp = await _setup(db_session)
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 5, 10), fecha_hasta=date(2026, 5, 15),
    ), actor=rrhh)
    lic = await enviar(db_session, lic_id=lic.id, actor=rrhh)
    lic = await rechazar(db_session, lic_id=lic.id, payload=RechazarIn(motivo_rechazo="no corresponde"), actor=medico)
    assert lic.estado == EstadoLicencia.RECHAZADO
    assert lic.motivo_rechazo == "no corresponde"


@pytest.mark.asyncio
async def test_validar_borrador_falla(db_session):
    rrhh, medico, _, tipo, emp = await _setup(db_session)
    lic = await crear_licencia(db_session, payload=LicenciaCreate(
        empleado_id=emp.id, tipo_licencia_id=tipo.id,
        fecha_desde=date(2026, 5, 10), fecha_hasta=date(2026, 5, 15),
    ), actor=rrhh)
    with pytest.raises(InvalidStateTransition):
        await validar(db_session, lic_id=lic.id, payload=ValidarIn(dias_otorgados=6), actor=medico)
