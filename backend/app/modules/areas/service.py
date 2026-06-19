from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.areas import repository as repo
from app.modules.areas.models import Area
from app.modules.areas.schemas import AreaCreate, AreaUpdate
from app.shared.exceptions import ConflictError, NotFoundError


async def create_area(s: AsyncSession, payload: AreaCreate) -> Area:
    if await repo.by_name(s, payload.nombre):
        raise ConflictError("area exists", detail={"field": "nombre"})
    if payload.parent_id and not await repo.get(s, payload.parent_id):
        raise NotFoundError("parent area not found")
    return await repo.insert(s, Area(nombre=payload.nombre, parent_id=payload.parent_id))


async def update_area(s: AsyncSession, id_: UUID, payload: AreaUpdate) -> Area:
    area = await repo.get(s, id_)
    if not area:
        raise NotFoundError("area no encontrada")
    updates = payload.model_dump(exclude_unset=True)
    if "nombre" in updates and updates["nombre"] != area.nombre:
        existing = await repo.by_name(s, updates["nombre"])
        if existing:
            raise ConflictError("area exists", detail={"field": "nombre"})
    if "parent_id" in updates and updates["parent_id"]:
        if not await repo.get(s, updates["parent_id"]):
            raise NotFoundError("parent area not found")
    return await repo.update(s, area, **updates)


async def delete_area(s: AsyncSession, id_: UUID) -> None:
    area = await repo.get(s, id_)
    if not area:
        raise NotFoundError("area no encontrada")
    from sqlalchemy import select, func
    from app.modules.empleados.models import Empleado
    count = (await s.execute(
        select(func.count()).where(Empleado.area_id == id_)
    )).scalar_one()
    if count > 0:
        raise ConflictError("area tiene empleados asignados", detail={"empleados": count})
    await repo.delete(s, area)
