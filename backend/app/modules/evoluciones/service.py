from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evoluciones import repository as repo
from app.modules.evoluciones.models import Evolucion
from app.modules.evoluciones.schemas import EvolucionCreate, EvolucionUpdate
from app.modules.atenciones import repository as aten_repo
from app.shared.exceptions import NotFoundError


async def create_evolucion(s: AsyncSession, payload: EvolucionCreate, medico_id: UUID) -> Evolucion:
    if not await aten_repo.get(s, payload.atencion_id):
        raise NotFoundError("atencion no encontrada")
    return await repo.insert(s, Evolucion(
        atencion_id=payload.atencion_id,
        motivo_consulta=payload.motivo_consulta,
        anamnesis=payload.anamnesis,
        examen_fisico=payload.examen_fisico,
        diagnostico_presuntivo=payload.diagnostico_presuntivo,
        diagnostico_definitivo=payload.diagnostico_definitivo,
        tratamiento=payload.tratamiento,
        observaciones=payload.observaciones,
        medico_id=medico_id,
    ))


async def update_evolucion(s: AsyncSession, id_: UUID, payload: EvolucionUpdate) -> Evolucion:
    ev = await repo.get(s, id_)
    if not ev:
        raise NotFoundError("evolucion no encontrada")
    updates = payload.model_dump(exclude_unset=True)
    return await repo.update(s, ev, **updates)
