from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.areas import repository as repo
from app.modules.areas.schemas import AreaCreate, AreaOut
from app.modules.areas.service import create_area
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/areas", tags=["areas"])


@router.get("", response_model=list[AreaOut])
async def list_areas(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.post(
    "", response_model=AreaOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH))],
)
async def create(payload: AreaCreate, s: AsyncSession = Depends(get_db)):
    return await create_area(s, payload)
