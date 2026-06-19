from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.atenciones import repository as repo
from app.modules.atenciones.models import EstadoAtencion
from app.modules.atenciones.schemas import AtencionCreate, AtencionOut, AtencionUpdate, CompletarIn
from app.modules.atenciones.service import (
    cancelar_atencion,
    completar_atencion,
    create_atencion,
    update_atencion,
)
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/atenciones", tags=["atenciones"])


@router.get("", response_model=list[AtencionOut])
async def list_atenciones(
    empleado_id: UUID | None = Query(default=None),
    medico_id: UUID | None = Query(default=None),
    estado: EstadoAtencion | None = Query(default=None),
    fecha: date | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    return await repo.list_(s, empleado_id=empleado_id, medico_id=medico_id,
                            estado=estado, fecha=fecha, limit=limit, offset=offset)


@router.get("/{id_}", response_model=AtencionOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db), _user: Usuario = Depends(current_user)):
    a = await repo.get_enriched(s, id_)
    if not a:
        raise NotFoundError("atencion no encontrada")
    return a


@router.post(
    "", response_model=AtencionOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))],
)
async def create(
    payload: AtencionCreate,
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    return await create_atencion(s, payload, user)


@router.put(
    "/{id_}", response_model=AtencionOut,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH))],
)
async def update(id_: UUID, payload: AtencionUpdate, s: AsyncSession = Depends(get_db)):
    return await update_atencion(s, id_, payload)


@router.post(
    "/{id_}/completar", response_model=AtencionOut,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.MEDICO))],
)
async def completar(id_: UUID, payload: CompletarIn, s: AsyncSession = Depends(get_db)):
    return await completar_atencion(s, id_, payload)


@router.post(
    "/{id_}/cancelar", response_model=AtencionOut,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH))],
)
async def cancelar(id_: UUID, s: AsyncSession = Depends(get_db)):
    return await cancelar_atencion(s, id_)
