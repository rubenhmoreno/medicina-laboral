from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.configuracion import repository as repo
from app.modules.configuracion.schemas import ConfiguracionOut, ConfiguracionUpdate
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/configuracion", tags=["configuracion"])


@router.get("", response_model=list[ConfiguracionOut])
async def list_configuracion(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.put(
    "/{clave}",
    response_model=ConfiguracionOut,
    dependencies=[Depends(require_role(Rol.ADMIN))],
)
async def update_configuracion(
    clave: str,
    payload: ConfiguracionUpdate,
    s: AsyncSession = Depends(get_db),
):
    row = await repo.get_by_clave(s, clave)
    if not row:
        raise NotFoundError(f"configuracion '{clave}' no encontrada")
    row.valor = payload.valor
    await s.flush()
    return row
