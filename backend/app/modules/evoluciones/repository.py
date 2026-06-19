from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evoluciones.models import Evolucion


async def insert(s: AsyncSession, ev: Evolucion) -> Evolucion:
    s.add(ev); await s.flush(); return ev


async def get(s: AsyncSession, id_: UUID) -> Evolucion | None:
    return (await s.execute(select(Evolucion).where(Evolucion.id == id_))).scalar_one_or_none()


async def list_by_atencion(s: AsyncSession, atencion_id: UUID) -> list[Evolucion]:
    return list((await s.execute(
        select(Evolucion).where(Evolucion.atencion_id == atencion_id).order_by(Evolucion.created_at.desc())
    )).scalars())


async def update(s: AsyncSession, ev: Evolucion, **kwargs: object) -> Evolucion:
    for k, v in kwargs.items():
        setattr(ev, k, v)
    await s.flush()
    return ev
