from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categorias import repository as cats_repo
from app.modules.empleados import repository as repo
from app.modules.empleados.models import Empleado
from app.modules.empleados.schemas import EmpleadoCreate
from app.shared.exceptions import ConflictError, NotFoundError


async def create_empleado(s: AsyncSession, payload: EmpleadoCreate) -> Empleado:
    if await repo.by_legajo(s, payload.legajo):
        raise ConflictError("legajo en uso", detail={"field": "legajo"})
    if await repo.by_cuil(s, payload.cuil):
        raise ConflictError("cuil en uso", detail={"field": "cuil"})
    if not await cats_repo.get(s, payload.categoria_id):
        raise NotFoundError("categoria no encontrada", detail={"categoria_id": str(payload.categoria_id)})
    return await repo.insert(s, Empleado(**payload.model_dump()))
