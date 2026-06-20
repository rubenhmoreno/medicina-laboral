from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.configuracion.models import Configuracion


async def list_all(s: AsyncSession) -> list[Configuracion]:
    result = await s.execute(select(Configuracion).order_by(Configuracion.clave))
    return list(result.scalars().all())


async def get_by_clave(s: AsyncSession, clave: str) -> Configuracion | None:
    result = await s.execute(select(Configuracion).where(Configuracion.clave == clave))
    return result.scalar_one_or_none()


async def get_dict(s: AsyncSession) -> dict[str, str]:
    rows = await list_all(s)
    return {r.clave: r.valor for r in rows}
