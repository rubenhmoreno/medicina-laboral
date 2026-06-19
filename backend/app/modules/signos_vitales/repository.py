from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.signos_vitales.models import SignosVitales


async def insert(s: AsyncSession, sv: SignosVitales) -> SignosVitales:
    s.add(sv); await s.flush(); return sv


async def get(s: AsyncSession, id_: UUID) -> SignosVitales | None:
    return (await s.execute(select(SignosVitales).where(SignosVitales.id == id_))).scalar_one_or_none()


async def get_by_atencion(s: AsyncSession, atencion_id: UUID) -> SignosVitales | None:
    return (await s.execute(
        select(SignosVitales).where(SignosVitales.atencion_id == atencion_id)
    )).scalar_one_or_none()


async def update(s: AsyncSession, sv: SignosVitales, **kwargs: object) -> SignosVitales:
    for k, v in kwargs.items():
        setattr(sv, k, v)
    await s.flush()
    return sv
