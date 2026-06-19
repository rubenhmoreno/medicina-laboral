from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categorias import repository as repo
from app.modules.categorias.models import CategoriaLaboral
from app.modules.categorias.schemas import CategoriaCreate, CategoriaUpdate
from app.shared.exceptions import ConflictError, NotFoundError


async def create_categoria(s: AsyncSession, p: CategoriaCreate) -> CategoriaLaboral:
    if await repo.by_codigo(s, p.codigo):
        raise ConflictError("categoria exists", detail={"field": "codigo"})
    return await repo.insert(s, CategoriaLaboral(codigo=p.codigo, nombre=p.nombre))


async def update_categoria(s: AsyncSession, id_: UUID, p: CategoriaUpdate) -> CategoriaLaboral:
    cat = await repo.get(s, id_)
    if not cat:
        raise NotFoundError("categoria no encontrada")
    updates = p.model_dump(exclude_unset=True)
    if "codigo" in updates and updates["codigo"] != cat.codigo:
        if await repo.by_codigo(s, updates["codigo"]):
            raise ConflictError("codigo en uso", detail={"field": "codigo"})
    return await repo.update(s, cat, **updates)


async def delete_categoria(s: AsyncSession, id_: UUID) -> None:
    cat = await repo.get(s, id_)
    if not cat:
        raise NotFoundError("categoria no encontrada")
    from sqlalchemy import select, func
    from app.modules.empleados.models import Empleado
    count = (await s.execute(
        select(func.count()).where(Empleado.categoria_id == id_)
    )).scalar_one()
    if count > 0:
        raise ConflictError("categoria tiene empleados asignados", detail={"empleados": count})
    await repo.delete(s, cat)
