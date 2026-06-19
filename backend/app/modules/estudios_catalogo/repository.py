from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estudios_catalogo.models import EstudioCatalogo, TipoEstudio


async def insert(s: AsyncSession, e: EstudioCatalogo) -> EstudioCatalogo:
    s.add(e); await s.flush(); return e


async def get(s: AsyncSession, id_: UUID) -> EstudioCatalogo | None:
    return (await s.execute(select(EstudioCatalogo).where(EstudioCatalogo.id == id_))).scalar_one_or_none()


async def list_(
    s: AsyncSession,
    *,
    tipo: TipoEstudio | None = None,
    activo: bool | None = None,
) -> list[EstudioCatalogo]:
    stmt = select(EstudioCatalogo).order_by(EstudioCatalogo.nombre)
    if tipo:
        stmt = stmt.where(EstudioCatalogo.tipo == tipo)
    if activo is not None:
        stmt = stmt.where(EstudioCatalogo.activo == activo)
    return list((await s.execute(stmt)).scalars())


async def update(s: AsyncSession, e: EstudioCatalogo, **kwargs: object) -> EstudioCatalogo:
    for k, v in kwargs.items():
        setattr(e, k, v)
    await s.flush()
    return e
