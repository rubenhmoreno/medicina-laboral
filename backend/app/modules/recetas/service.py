from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recetas import repository as repo
from app.modules.recetas.models import ItemReceta, Receta
from app.modules.recetas.schemas import RecetaCreate
from app.modules.atenciones import repository as aten_repo
from app.shared.exceptions import NotFoundError


async def create_receta(s: AsyncSession, payload: RecetaCreate, medico_id: UUID) -> Receta:
    if not await aten_repo.get(s, payload.atencion_id):
        raise NotFoundError("atencion no encontrada")
    receta = Receta(
        atencion_id=payload.atencion_id,
        medico_id=medico_id,
        diagnostico=payload.diagnostico,
        observaciones=payload.observaciones,
    )
    for idx, item in enumerate(payload.items):
        receta.items.append(ItemReceta(
            medicamento=item.medicamento,
            dosis=item.dosis,
            frecuencia=item.frecuencia,
            duracion=item.duracion,
            orden=idx,
        ))
    return await repo.insert(s, receta)
