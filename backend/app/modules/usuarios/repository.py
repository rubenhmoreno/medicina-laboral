# backend/app/modules/usuarios/repository.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.usuarios.models import Usuario


async def get_by_email(session: AsyncSession, email: str) -> Usuario | None:
    res = await session.execute(select(Usuario).where(Usuario.email == email))
    return res.scalar_one_or_none()


async def get_by_id(session: AsyncSession, id_: UUID) -> Usuario | None:
    res = await session.execute(select(Usuario).where(Usuario.id == id_))
    return res.scalar_one_or_none()


async def insert(session: AsyncSession, u: Usuario) -> Usuario:
    session.add(u)
    await session.flush()
    return u


async def update(session: AsyncSession, u: Usuario) -> Usuario:
    await session.flush()
    return u


async def list_all(session: AsyncSession) -> list[Usuario]:
    res = await session.execute(select(Usuario).order_by(Usuario.email))
    return list(res.scalars())
