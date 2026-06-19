from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.areas import repository as repo
from app.modules.areas.schemas import AreaCreate, AreaOut, AreaUpdate
from app.modules.areas.service import create_area, update_area, delete_area
from app.modules.usuarios.models import Rol
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/areas", tags=["areas"])


@router.get("", response_model=list[AreaOut])
async def list_areas(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.get("/{id_}", response_model=AreaOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db)):
    area = await repo.get(s, id_)
    if not area:
        raise NotFoundError("area no encontrada")
    return area


@router.post(
    "", response_model=AreaOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH))],
)
async def create(payload: AreaCreate, s: AsyncSession = Depends(get_db)):
    return await create_area(s, payload)


@router.put(
    "/{id_}", response_model=AreaOut,
    dependencies=[Depends(require_role(Rol.ADMIN))],
)
async def update(id_: UUID, payload: AreaUpdate, s: AsyncSession = Depends(get_db)):
    return await update_area(s, id_, payload)


@router.delete(
    "/{id_}", status_code=204,
    dependencies=[Depends(require_role(Rol.ADMIN))],
)
async def delete(id_: UUID, s: AsyncSession = Depends(get_db)):
    await delete_area(s, id_)
