from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.categorias import repository as repo
from app.modules.categorias.schemas import CategoriaCreate, CategoriaOut
from app.modules.categorias.service import create_categoria
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/categorias", tags=["categorias"])


@router.get("", response_model=list[CategoriaOut])
async def list_categorias(s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s)


@router.post("", response_model=CategoriaOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def create(p: CategoriaCreate, s: AsyncSession = Depends(get_db)):
    return await create_categoria(s, p)
