from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.evoluciones import repository as repo
from app.modules.evoluciones.schemas import EvolucionCreate, EvolucionOut, EvolucionUpdate
from app.modules.evoluciones.service import create_evolucion, update_evolucion
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/evoluciones", tags=["evoluciones"])


@router.post(
    "", response_model=EvolucionOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.MEDICO))],
)
async def create(
    payload: EvolucionCreate,
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    return await create_evolucion(s, payload, user.id)


@router.get("/by-atencion/{atencion_id}", response_model=list[EvolucionOut])
async def list_by_atencion(
    atencion_id: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    return await repo.list_by_atencion(s, atencion_id)


@router.get("/{id_}", response_model=EvolucionOut)
async def get_one(
    id_: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    ev = await repo.get(s, id_)
    if not ev:
        raise NotFoundError("evolucion no encontrada")
    return ev


@router.put(
    "/{id_}", response_model=EvolucionOut,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.MEDICO))],
)
async def update(
    id_: UUID,
    payload: EvolucionUpdate,
    s: AsyncSession = Depends(get_db),
):
    return await update_evolucion(s, id_, payload)
