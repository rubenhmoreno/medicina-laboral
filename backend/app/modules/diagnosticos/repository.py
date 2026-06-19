from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.diagnosticos.models import Diagnostico


async def list_all(s: AsyncSession, categoria: str | None = None) -> list[Diagnostico]:
    stmt = select(Diagnostico).order_by(Diagnostico.descripcion)
    if categoria:
        stmt = stmt.where(Diagnostico.categoria == categoria)
    return list((await s.execute(stmt)).scalars())

async def get(s: AsyncSession, id_: UUID) -> Diagnostico | None:
    return (await s.execute(select(Diagnostico).where(Diagnostico.id == id_))).scalar_one_or_none()

async def insert(s: AsyncSession, d: Diagnostico) -> Diagnostico:
    s.add(d); await s.flush(); return d
