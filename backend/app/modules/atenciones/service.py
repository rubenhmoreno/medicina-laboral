from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.atenciones import repository as repo
from app.modules.atenciones.models import Atencion, EstadoAtencion
from app.modules.atenciones.schemas import AtencionCreate, AtencionUpdate, CompletarIn
from app.modules.empleados import repository as emp_repo
from app.modules.usuarios import repository as users_repo
from app.shared.exceptions import ConflictError, NotFoundError

if TYPE_CHECKING:
    from app.modules.usuarios.models import Usuario


async def create_atencion(s: AsyncSession, payload: AtencionCreate, actor: "Usuario") -> Atencion:
    from app.modules.usuarios.models import Rol
    if not await emp_repo.get(s, payload.empleado_id):
        raise NotFoundError("empleado no encontrado")
    # Auto-assign medico_id when the actor is a doctor
    medico_id = payload.medico_id
    if actor.rol == Rol.MEDICO:
        medico_id = actor.id
    if medico_id:
        medico = await users_repo.get_by_id(s, medico_id)
        if not medico:
            raise NotFoundError("medico no encontrado")
    return await repo.insert(s, Atencion(
        empleado_id=payload.empleado_id,
        asignado_por=actor.id,
        medico_id=medico_id,
        fecha_turno=payload.fecha_turno,
        motivo=payload.motivo,
        estado=EstadoAtencion.PENDIENTE,
    ))


async def update_atencion(s: AsyncSession, id_: UUID, payload: AtencionUpdate) -> Atencion:
    atencion = await repo.get(s, id_)
    if not atencion:
        raise NotFoundError("atencion no encontrada")
    if atencion.estado != EstadoAtencion.PENDIENTE:
        raise ConflictError("solo se pueden editar atenciones pendientes")
    updates = payload.model_dump(exclude_unset=True)
    if "medico_id" in updates and updates["medico_id"]:
        if not await users_repo.get_by_id(s, updates["medico_id"]):
            raise NotFoundError("medico no encontrado")
    return await repo.update(s, atencion, **updates)


async def completar_atencion(s: AsyncSession, id_: UUID, payload: CompletarIn) -> Atencion:
    atencion = await repo.get(s, id_)
    if not atencion:
        raise NotFoundError("atencion no encontrada")
    if atencion.estado != EstadoAtencion.PENDIENTE:
        raise ConflictError("la atencion no esta pendiente")
    return await repo.update(s, atencion,
                             estado=EstadoAtencion.COMPLETADA,
                             notas_medicas=payload.notas_medicas)


async def cancelar_atencion(s: AsyncSession, id_: UUID) -> Atencion:
    atencion = await repo.get(s, id_)
    if not atencion:
        raise NotFoundError("atencion no encontrada")
    if atencion.estado != EstadoAtencion.PENDIENTE:
        raise ConflictError("la atencion no esta pendiente")
    return await repo.update(s, atencion, estado=EstadoAtencion.CANCELADA)
