from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estudios_catalogo import repository as repo
from app.modules.estudios_catalogo.models import EstudioCatalogo, TipoEstudio
from app.modules.estudios_catalogo.schemas import EstudioCatalogoCreate, EstudioCatalogoUpdate
from app.shared.exceptions import NotFoundError


async def create_estudio(s: AsyncSession, payload: EstudioCatalogoCreate) -> EstudioCatalogo:
    return await repo.insert(s, EstudioCatalogo(
        nombre=payload.nombre,
        codigo=payload.codigo,
        tipo=TipoEstudio(payload.tipo),
        categoria=payload.categoria,
        activo=payload.activo,
    ))


async def update_estudio(s: AsyncSession, id_: UUID, payload: EstudioCatalogoUpdate) -> EstudioCatalogo:
    est = await repo.get(s, id_)
    if not est:
        raise NotFoundError("estudio no encontrado")
    updates = payload.model_dump(exclude_unset=True)
    if "tipo" in updates and updates["tipo"]:
        updates["tipo"] = TipoEstudio(updates["tipo"])
    return await repo.update(s, est, **updates)
