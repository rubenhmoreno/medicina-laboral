from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.empleados import repository as repo
from app.modules.empleados.schemas import EmpleadoCreate, EmpleadoOut
from app.modules.empleados.service import create_empleado
from app.modules.usuarios.models import Rol
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/empleados", tags=["empleados"])


@router.get("", response_model=list[EmpleadoOut])
async def list_empleados(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    s: AsyncSession = Depends(get_db),
):
    return await repo.list_(s, q=q, limit=limit, offset=offset)


@router.get("/{id_}", response_model=EmpleadoOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db)):
    e = await repo.get(s, id_)
    if not e:
        raise NotFoundError("empleado no encontrado")
    return e


@router.post(
    "", response_model=EmpleadoOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH))],
)
async def create(payload: EmpleadoCreate, s: AsyncSession = Depends(get_db)):
    return await create_empleado(s, payload)
