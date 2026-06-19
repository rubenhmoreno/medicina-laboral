from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.estudios_catalogo import repository as repo
from app.modules.estudios_catalogo.models import TipoEstudio
from app.modules.estudios_catalogo.schemas import (
    EstudioCatalogoCreate,
    EstudioCatalogoOut,
    EstudioCatalogoUpdate,
)
from app.modules.estudios_catalogo.service import create_estudio, update_estudio
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(prefix="/api/estudios-catalogo", tags=["estudios-catalogo"])


@router.get("", response_model=list[EstudioCatalogoOut])
async def list_estudios(
    tipo: TipoEstudio | None = Query(default=None),
    activo: bool | None = Query(default=None),
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    return await repo.list_(s, tipo=tipo, activo=activo)


@router.post(
    "", response_model=EstudioCatalogoOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN))],
)
async def create(
    payload: EstudioCatalogoCreate,
    s: AsyncSession = Depends(get_db),
):
    return await create_estudio(s, payload)


@router.put(
    "/{id_}", response_model=EstudioCatalogoOut,
    dependencies=[Depends(require_role(Rol.ADMIN))],
)
async def update(
    id_: UUID,
    payload: EstudioCatalogoUpdate,
    s: AsyncSession = Depends(get_db),
):
    return await update_estudio(s, id_, payload)
