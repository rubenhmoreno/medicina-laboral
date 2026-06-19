from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.topes import repository as repo
from app.modules.topes.schemas import TopeOut, TopeSet
from app.modules.topes.service import set_tope
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/admin/topes", tags=["topes"],
                   dependencies=[Depends(require_role(Rol.ADMIN))])


@router.get("", response_model=list[TopeOut])
async def listar(s: AsyncSession = Depends(get_db)):
    return await repo.listar_actuales(s)


@router.put("/{categoria_id}/{tipo_licencia_id}", response_model=TopeOut)
async def upsert(
    categoria_id: UUID,
    tipo_licencia_id: UUID,
    payload: TopeSet,
    s: AsyncSession = Depends(get_db),
):
    return await set_tope(s, categoria_id, tipo_licencia_id, payload)
