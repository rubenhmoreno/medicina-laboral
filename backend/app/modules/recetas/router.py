from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.recetas import repository as repo
from app.modules.recetas.schemas import RecetaCreate, RecetaOut
from app.modules.recetas.service import create_receta
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/recetas", tags=["recetas"])


@router.post(
    "", response_model=RecetaOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.MEDICO))],
)
async def create(
    payload: RecetaCreate,
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    return await create_receta(s, payload, user.id)


@router.get("/by-atencion/{atencion_id}", response_model=list[RecetaOut])
async def list_by_atencion(
    atencion_id: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    return await repo.list_by_atencion(s, atencion_id)


@router.get("/{id_}", response_model=RecetaOut)
async def get_one(
    id_: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    r = await repo.get(s, id_)
    if not r:
        raise NotFoundError("receta no encontrada")
    return r
