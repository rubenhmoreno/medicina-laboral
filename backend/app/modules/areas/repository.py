from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.areas.models import Area


async def list_all(s: AsyncSession) -> list[Area]:
    return list((await s.execute(select(Area).order_by(Area.nombre))).scalars())


async def get(s: AsyncSession, id_: UUID) -> Area | None:
    return (await s.execute(select(Area).where(Area.id == id_))).scalar_one_or_none()


async def by_name(s: AsyncSession, nombre: str) -> Area | None:
    return (await s.execute(select(Area).where(Area.nombre == nombre))).scalar_one_or_none()


async def insert(s: AsyncSession, a: Area) -> Area:
    s.add(a); await s.flush(); return a
