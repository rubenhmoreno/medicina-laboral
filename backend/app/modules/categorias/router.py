from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.categorias import repository as repo
from app.modules.categorias.schemas import CategoriaCreate, CategoriaOut, CategoriaUpdate
from app.modules.categorias.service import create_categoria, update_categoria, delete_categoria
from app.modules.usuarios.models import Rol
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaOut])
async def list_categorias(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.get("/{id_}", response_model=CategoriaOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db)):
    cat = await repo.get(s, id_)
    if not cat:
        raise NotFoundError("categoria no encontrada")
    return cat


@router.post("", response_model=CategoriaOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def create(p: CategoriaCreate, s: AsyncSession = Depends(get_db)):
    return await create_categoria(s, p)


@router.put("/{id_}", response_model=CategoriaOut,
            dependencies=[Depends(require_role(Rol.ADMIN))])
async def update(id_: UUID, p: CategoriaUpdate, s: AsyncSession = Depends(get_db)):
    return await update_categoria(s, id_, p)


@router.delete("/{id_}", status_code=204,
               dependencies=[Depends(require_role(Rol.ADMIN))])
async def delete(id_: UUID, s: AsyncSession = Depends(get_db)):
    await delete_categoria(s, id_)
