from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.empleados.models import Empleado


async def list_(s: AsyncSession, q: str | None = None, limit: int = 50, offset: int = 0) -> list[Empleado]:
    stmt = select(Empleado).order_by(Empleado.apellido, Empleado.nombre).limit(limit).offset(offset)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            Empleado.legajo.ilike(like),
            Empleado.cuil.ilike(like),
            Empleado.apellido.ilike(like),
            Empleado.nombre.ilike(like),
        ))
    return list((await s.execute(stmt)).scalars())


async def count(s: AsyncSession) -> int:
    result = await s.execute(select(func.count()).select_from(Empleado))
    return result.scalar_one()


async def get(s: AsyncSession, id_: UUID) -> Empleado | None:
    return (await s.execute(select(Empleado).where(Empleado.id == id_))).scalar_one_or_none()


async def by_legajo(s: AsyncSession, legajo: str) -> Empleado | None:
    return (await s.execute(select(Empleado).where(Empleado.legajo == legajo))).scalar_one_or_none()


async def by_cuil(s: AsyncSession, cuil: str) -> Empleado | None:
    return (await s.execute(select(Empleado).where(Empleado.cuil == cuil))).scalar_one_or_none()


async def insert(s: AsyncSession, e: Empleado) -> Empleado:
    s.add(e); await s.flush(); return e


async def update(s: AsyncSession, e: Empleado, **kwargs: object) -> Empleado:
    for k, v in kwargs.items():
        setattr(e, k, v)
    await s.flush()
    return e
