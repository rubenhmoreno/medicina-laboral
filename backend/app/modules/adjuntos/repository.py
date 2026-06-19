from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.adjuntos.models import Adjunto


async def insert(s: AsyncSession, a: Adjunto) -> Adjunto:
    s.add(a); await s.flush(); return a


async def get(s: AsyncSession, id_: UUID) -> Adjunto | None:
    return (await s.execute(select(Adjunto).where(Adjunto.id == id_))).scalar_one_or_none()


async def list_for_licencia(s: AsyncSession, licencia_id: UUID) -> list[Adjunto]:
    stmt = select(Adjunto).where(Adjunto.licencia_id == licencia_id).order_by(Adjunto.created_at)
    return list((await s.execute(stmt)).scalars())
