from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.tipos_licencia import repository as repo
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate, TipoLicenciaOut, TipoLicenciaUpdate
from app.modules.tipos_licencia.service import create_tipo, update_tipo, delete_tipo
from app.modules.usuarios.models import Rol
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/tipos-licencia", tags=["tipos-licencia"])


@router.get("", response_model=list[TipoLicenciaOut])
async def list_(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.get("/{id_}", response_model=TipoLicenciaOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db)):
    tl = await repo.get(s, id_)
    if not tl:
        raise NotFoundError("tipo de licencia no encontrado")
    return tl


@router.post("", response_model=TipoLicenciaOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def create(p: TipoLicenciaCreate, s: AsyncSession = Depends(get_db)):
    return await create_tipo(s, p)


@router.put("/{id_}", response_model=TipoLicenciaOut,
            dependencies=[Depends(require_role(Rol.ADMIN))])
async def update(id_: UUID, p: TipoLicenciaUpdate, s: AsyncSession = Depends(get_db)):
    return await update_tipo(s, id_, p)


@router.delete("/{id_}", status_code=204,
               dependencies=[Depends(require_role(Rol.ADMIN))])
async def delete(id_: UUID, s: AsyncSession = Depends(get_db)):
    await delete_tipo(s, id_)
