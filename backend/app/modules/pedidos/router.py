from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.pedidos import repository as repo
from app.modules.pedidos.schemas import PedidoCreate, PedidoOut
from app.modules.pedidos.service import create_pedido
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/pedidos", tags=["pedidos"])


@router.post(
    "", response_model=PedidoOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.MEDICO))],
)
async def create(
    payload: PedidoCreate,
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    return await create_pedido(s, payload, user.id)


@router.get("/by-atencion/{atencion_id}", response_model=list[PedidoOut])
async def list_by_atencion(
    atencion_id: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    return await repo.list_by_atencion(s, atencion_id)


@router.get("/{id_}", response_model=PedidoOut)
async def get_one(
    id_: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    p = await repo.get(s, id_)
    if not p:
        raise NotFoundError("pedido no encontrado")
    return p
