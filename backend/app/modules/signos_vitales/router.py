from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.signos_vitales import repository as repo
from app.modules.signos_vitales.schemas import SignosVitalesCreate, SignosVitalesOut, SignosVitalesUpdate
from app.modules.signos_vitales.service import create_signos, update_signos
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(prefix="/api/signos-vitales", tags=["signos-vitales"])


@router.post(
    "", response_model=SignosVitalesOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.MEDICO))],
)
async def create(
    payload: SignosVitalesCreate,
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    return await create_signos(s, payload, user.id)


@router.get("/by-atencion/{atencion_id}", response_model=SignosVitalesOut | None)
async def get_by_atencion(
    atencion_id: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    return await repo.get_by_atencion(s, atencion_id)


@router.put(
    "/{id_}", response_model=SignosVitalesOut,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.MEDICO))],
)
async def update(
    id_: UUID,
    payload: SignosVitalesUpdate,
    s: AsyncSession = Depends(get_db),
):
    return await update_signos(s, id_, payload)
