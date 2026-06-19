from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.categorias import repository as repo
from app.modules.categorias.models import CategoriaLaboral
from app.modules.categorias.schemas import CategoriaCreate
from app.shared.exceptions import ConflictError


async def create_categoria(s: AsyncSession, p: CategoriaCreate) -> CategoriaLaboral:
    if await repo.by_codigo(s, p.codigo):
        raise ConflictError("categoria exists", detail={"field": "codigo"})
    return await repo.insert(s, CategoriaLaboral(codigo=p.codigo, nombre=p.nombre))
