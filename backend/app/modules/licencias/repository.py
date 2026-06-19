from datetime import date
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.licencias.models import EstadoLicencia, Licencia


async def insert(s: AsyncSession, lic: Licencia) -> Licencia:
    s.add(lic); await s.flush(); return lic


async def get(s: AsyncSession, id_: UUID) -> Licencia | None:
    return (await s.execute(select(Licencia).where(Licencia.id == id_))).scalar_one_or_none()


async def list_(
    s: AsyncSession,
    *,
    estado: EstadoLicencia | None = None,
    empleado_id: UUID | None = None,
    area_id: UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Licencia]:
    stmt = select(Licencia).order_by(Licencia.fecha_desde.desc()).limit(limit).offset(offset)
    conds = []
    if estado:
        conds.append(Licencia.estado == estado)
    if empleado_id:
        conds.append(Licencia.empleado_id == empleado_id)
    if desde:
        conds.append(Licencia.fecha_desde >= desde)
    if hasta:
        conds.append(Licencia.fecha_desde <= hasta)
    if conds:
        stmt = stmt.where(and_(*conds))
    if area_id:
        from app.modules.empleados.models import Empleado
        stmt = stmt.join(Empleado, Empleado.id == Licencia.empleado_id).where(Empleado.area_id == area_id)
    return list((await s.execute(stmt)).scalars())
