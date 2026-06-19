from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.reportes import repository as repo


async def por_area(s: AsyncSession, desde: date, hasta: date):
    return await repo.ausentismo_por_area(s, desde, hasta)


async def por_categoria_diag(s: AsyncSession, desde: date, hasta: date):
    return await repo.ausentismo_por_categoria_diag(s, desde, hasta)


async def por_mes(s: AsyncSession, desde: date, hasta: date):
    return await repo.frecuencia_mensual(s, desde, hasta)
