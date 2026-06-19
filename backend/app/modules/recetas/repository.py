from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.recetas.models import Receta


async def insert(s: AsyncSession, r: Receta) -> Receta:
    s.add(r); await s.flush(); await s.refresh(r, ["items"]); return r


async def get(s: AsyncSession, id_: UUID) -> Receta | None:
    return (await s.execute(
        select(Receta).options(selectinload(Receta.items)).where(Receta.id == id_)
    )).scalar_one_or_none()


async def list_by_atencion(s: AsyncSession, atencion_id: UUID) -> list[Receta]:
    return list((await s.execute(
        select(Receta).options(selectinload(Receta.items))
        .where(Receta.atencion_id == atencion_id)
        .order_by(Receta.created_at.desc())
    )).scalars())
