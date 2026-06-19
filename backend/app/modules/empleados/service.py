from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.areas import repository as areas_repo
from app.modules.categorias import repository as cats_repo
from app.modules.empleados import repository as repo
from app.modules.empleados.models import Empleado
from app.modules.empleados.schemas import EmpleadoCreate, EmpleadoUpdate
from app.shared.exceptions import ConflictError, NotFoundError


async def create_empleado(s: AsyncSession, payload: EmpleadoCreate) -> Empleado:
    if await repo.by_legajo(s, payload.legajo):
        raise ConflictError("legajo en uso", detail={"field": "legajo"})
    if await repo.by_cuil(s, payload.cuil):
        raise ConflictError("cuil en uso", detail={"field": "cuil"})
    if not await cats_repo.get(s, payload.categoria_id):
        raise NotFoundError("categoria no encontrada", detail={"categoria_id": str(payload.categoria_id)})
    if payload.area_id and not await areas_repo.get(s, payload.area_id):
        raise NotFoundError("area no encontrada", detail={"area_id": str(payload.area_id)})
    return await repo.insert(s, Empleado(**payload.model_dump()))


async def update_empleado(s: AsyncSession, id_: UUID, payload: EmpleadoUpdate) -> Empleado:
    emp = await repo.get(s, id_)
    if not emp:
        raise NotFoundError("empleado no encontrado")
    updates = payload.model_dump(exclude_unset=True)
    if "categoria_id" in updates and updates["categoria_id"]:
        if not await cats_repo.get(s, updates["categoria_id"]):
            raise NotFoundError("categoria no encontrada")
    if "area_id" in updates and updates["area_id"]:
        if not await areas_repo.get(s, updates["area_id"]):
            raise NotFoundError("area no encontrada")
    return await repo.update(s, emp, **updates)
