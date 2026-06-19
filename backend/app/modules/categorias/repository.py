from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.categorias.models import CategoriaLaboral


async def list_all(s: AsyncSession) -> list[CategoriaLaboral]:
    return list((await s.execute(select(CategoriaLaboral).order_by(CategoriaLaboral.codigo))).scalars())

async def by_codigo(s: AsyncSession, codigo: str) -> CategoriaLaboral | None:
    return (await s.execute(select(CategoriaLaboral).where(CategoriaLaboral.codigo == codigo))).scalar_one_or_none()

async def get(s: AsyncSession, id_: UUID) -> CategoriaLaboral | None:
    return (await s.execute(select(CategoriaLaboral).where(CategoriaLaboral.id == id_))).scalar_one_or_none()

async def insert(s: AsyncSession, c: CategoriaLaboral) -> CategoriaLaboral:
    s.add(c); await s.flush(); return c
