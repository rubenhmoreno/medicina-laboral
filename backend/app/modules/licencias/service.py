from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auditoria import repository as audit_repo
from app.modules.empleados import repository as emp_repo
from app.modules.licencias import repository as repo
from app.modules.licencias.calculo import calcular_dias, evaluar_tope
from app.modules.licencias.models import EstadoLicencia, Licencia, OrigenLicencia
from app.modules.licencias.schemas import (
    AnularIn,
    LicenciaCreate,
    RechazarIn,
    ValidarIn,
)
from app.modules.licencias.state_machine import next_state
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError, ValidationError


def _origen_for(rol: Rol) -> OrigenLicencia:
    return OrigenLicencia.MEDICO if rol == Rol.MEDICO else OrigenLicencia.RRHH


async def _record_state_change(
    s: AsyncSession, *, lic: Licencia, frm: EstadoLicencia, to: EstadoLicencia, actor: Usuario, extra: dict | None = None
) -> None:
    payload = {"from": frm.value, "to": to.value}
    if extra:
        payload.update(extra)
    await audit_repo.append(
        s, accion="state_change", entidad="licencia",
        usuario_id=actor.id, entidad_id=lic.id, payload=payload,
        ip=None, user_agent=None,
    )


async def crear_licencia(s: AsyncSession, *, payload: LicenciaCreate, actor: Usuario) -> Licencia:
    emp = await emp_repo.get(s, payload.empleado_id)
    if emp is None:
        raise NotFoundError("empleado no encontrado")
    dias = calcular_dias(payload.fecha_desde, payload.fecha_hasta)
    if dias <= 0:
        raise ValidationError("rango de fechas inválido")
    lic = Licencia(
        empleado_id=payload.empleado_id,
        tipo_licencia_id=payload.tipo_licencia_id,
        diagnostico=payload.diagnostico,
        fecha_desde=payload.fecha_desde,
        fecha_hasta=payload.fecha_hasta,
        dias_solicitados=dias,
        estado=EstadoLicencia.BORRADOR,
        origen=_origen_for(actor.rol),
        observaciones=payload.observaciones,
        certificante=payload.certificante,
        matricula_certificante=payload.matricula_certificante,
        creado_por=actor.id,
    )
    return await repo.insert(s, lic)


async def enviar(s: AsyncSession, *, lic_id: UUID, actor: Usuario) -> Licencia:
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    frm = lic.estado
    lic.estado = next_state(frm, "enviar", actor.rol)
    await s.flush()
    await _record_state_change(s, lic=lic, frm=frm, to=lic.estado, actor=actor)
    return lic


async def validar(
    s: AsyncSession, *, lic_id: UUID, payload: ValidarIn, actor: Usuario
) -> Licencia:
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    frm = lic.estado
    lic.estado = next_state(frm, "validar", actor.rol)
    lic.dias_otorgados = payload.dias_otorgados
    lic.modo_constatacion = payload.modo_constatacion
    if payload.observaciones:
        lic.observaciones = (lic.observaciones or "") + f"\n[validación] {payload.observaciones}"
    lic.validado_por = actor.id
    lic.validado_en = datetime.now(timezone.utc)
    await s.flush()
    await _record_state_change(s, lic=lic, frm=frm, to=lic.estado, actor=actor, extra={"dias_otorgados": payload.dias_otorgados})
    return lic


async def rechazar(
    s: AsyncSession, *, lic_id: UUID, payload: RechazarIn, actor: Usuario
) -> Licencia:
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    frm = lic.estado
    lic.estado = next_state(frm, "rechazar", actor.rol)
    lic.motivo_rechazo = payload.motivo_rechazo
    await s.flush()
    await _record_state_change(s, lic=lic, frm=frm, to=lic.estado, actor=actor, extra={"motivo_rechazo": payload.motivo_rechazo})
    return lic


async def anular(
    s: AsyncSession, *, lic_id: UUID, payload: AnularIn, actor: Usuario
) -> Licencia:
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    frm = lic.estado
    lic.estado = next_state(frm, "anular", actor.rol)
    lic.motivo_anulacion = payload.motivo_anulacion
    await s.flush()
    await _record_state_change(s, lic=lic, frm=frm, to=lic.estado, actor=actor, extra={"motivo_anulacion": payload.motivo_anulacion})
    return lic


async def evaluar_tope_para_licencia(
    s: AsyncSession, lic_id: UUID, fecha_ref=None
):
    lic = await repo.get(s, lic_id)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    emp = await emp_repo.get(s, lic.empleado_id)
    from datetime import date as _date
    return await evaluar_tope(
        s,
        empleado=emp,
        tipo_licencia_id=lic.tipo_licencia_id,
        dias_solicitados=lic.dias_solicitados,
        fecha_ref=fecha_ref or _date.today(),
    )
