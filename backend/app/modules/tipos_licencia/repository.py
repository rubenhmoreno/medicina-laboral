from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tipos_licencia.models import TipoLicencia


async def list_all(s: AsyncSession) -> list[TipoLicencia]:
    return list((await s.execute(select(TipoLicencia).order_by(TipoLicencia.codigo))).scalars())

async def by_codigo(s: AsyncSession, codigo: str) -> TipoLicencia | None:
    return (await s.execute(select(TipoLicencia).where(TipoLicencia.codigo == codigo))).scalar_one_or_none()

async def get(s: AsyncSession, id_: UUID) -> TipoLicencia | None:
    return (await s.execute(select(TipoLicencia).where(TipoLicencia.id == id_))).scalar_one_or_none()

async def insert(s: AsyncSession, t: TipoLicencia) -> TipoLicencia:
    s.add(t); await s.flush(); return t


async def update(s: AsyncSession, t: TipoLicencia, **kwargs: object) -> TipoLicencia:
    for k, v in kwargs.items():
        setattr(t, k, v)
    await s.flush()
    return t


async def delete(s: AsyncSession, t: TipoLicencia) -> None:
    await s.delete(t)
    await s.flush()
