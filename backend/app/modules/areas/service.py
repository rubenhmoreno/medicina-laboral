from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.areas import repository as repo
from app.modules.areas.models import Area
from app.modules.areas.schemas import AreaCreate
from app.shared.exceptions import ConflictError, NotFoundError


async def create_area(s: AsyncSession, payload: AreaCreate) -> Area:
    if await repo.by_name(s, payload.nombre):
        raise ConflictError("area exists", detail={"field": "nombre"})
    if payload.parent_id and not await repo.get(s, payload.parent_id):
        raise NotFoundError("parent area not found")
    return await repo.insert(s, Area(nombre=payload.nombre, parent_id=payload.parent_id))
