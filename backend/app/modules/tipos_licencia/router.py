from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.tipos_licencia import repository as repo
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate, TipoLicenciaOut
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/tipos-licencia", tags=["tipos-licencia"])


@router.get("", response_model=list[TipoLicenciaOut])
async def list_(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.post("", response_model=TipoLicenciaOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def create(p: TipoLicenciaCreate, s: AsyncSession = Depends(get_db)):
    return await create_tipo(s, p)
