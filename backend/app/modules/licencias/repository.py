from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.licencias.models import EstadoLicencia, Licencia


async def insert(s: AsyncSession, lic: Licencia) -> Licencia:
    s.add(lic); await s.flush(); return lic


async def get(s: AsyncSession, id_: UUID) -> Licencia | None:
    return (await s.execute(select(Licencia).where(Licencia.id == id_))).scalar_one_or_none()


async def get_enriched(s: AsyncSession, id_: UUID) -> Licencia | None:
    lic = await get(s, id_)
    if lic:
        await _enrich(s, [lic])
    return lic


async def count(
    s: AsyncSession,
    estado: EstadoLicencia | None = None,
    vigente: bool = False,
) -> int:
    stmt = select(func.count()).select_from(Licencia)
    if estado:
        stmt = stmt.where(Licencia.estado == estado)
    if vigente:
        hoy = date.today()
        stmt = stmt.where(and_(
            Licencia.estado == EstadoLicencia.VALIDADO,
            Licencia.fecha_desde <= hoy,
            Licencia.fecha_hasta >= hoy,
        ))
    return (await s.execute(stmt)).scalar_one()


async def list_(
    s: AsyncSession,
    *,
    estado: EstadoLicencia | None = None,
    empleado_id: UUID | None = None,
    area_id: UUID | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    vigente: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Licencia]:
    from app.modules.empleados.models import Empleado

    stmt = (
        select(Licencia)
        .join(Empleado, Empleado.id == Licencia.empleado_id)
        .order_by(Licencia.fecha_desde.desc(), Empleado.apellido, Empleado.nombre)
        .limit(limit)
        .offset(offset)
    )
    conds = []
    if vigente:
        hoy = date.today()
        conds.append(Licencia.estado == EstadoLicencia.VALIDADO)
        conds.append(Licencia.fecha_desde <= hoy)
        conds.append(Licencia.fecha_hasta >= hoy)
    elif estado:
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
        stmt = stmt.where(Empleado.area_id == area_id)
    rows = list((await s.execute(stmt)).scalars())
    await _enrich(s, rows)
    return rows


async def _enrich(s: AsyncSession, rows: list[Licencia]) -> None:
    """Attach enriched display fields from related tables."""
    if not rows:
        return

    from app.modules.areas.models import Area
    from app.modules.empleados.models import Empleado
    from app.modules.tipos_licencia.models import TipoLicencia
    from app.modules.usuarios.models import Usuario

    emp_ids = {r.empleado_id for r in rows}
    tipo_ids = {r.tipo_licencia_id for r in rows}
    user_ids = {r.creado_por for r in rows}
    user_ids |= {r.validado_por for r in rows if r.validado_por}

    # Empleados (full data)
    emp_map: dict[UUID, Empleado] = {}
    if emp_ids:
        result = await s.execute(select(Empleado).where(Empleado.id.in_(emp_ids)))
        for (emp,) in result:
            emp_map[emp.id] = emp

    # Areas
    area_ids = {e.area_id for e in emp_map.values() if e.area_id}
    area_map: dict[UUID, str] = {}
    if area_ids:
        result = await s.execute(select(Area.id, Area.nombre).where(Area.id.in_(area_ids)))
        for aid, nombre in result:
            area_map[aid] = nombre

    # Tipos licencia
    tipo_map: dict[UUID, str] = {}
    if tipo_ids:
        result = await s.execute(select(TipoLicencia.id, TipoLicencia.nombre).where(TipoLicencia.id.in_(tipo_ids)))
        for tid, nombre in result:
            tipo_map[tid] = nombre

    # Usuarios (creado_por / validado_por)
    user_map: dict[UUID, str] = {}
    if user_ids:
        result = await s.execute(select(Usuario.id, Usuario.nombre, Usuario.email).where(Usuario.id.in_(user_ids)))
        for uid, nombre, email in result:
            user_map[uid] = nombre or email

    for r in rows:
        emp = emp_map.get(r.empleado_id)
        r.empleado_nombre = f"{emp.apellido}, {emp.nombre}" if emp else None  # type: ignore[attr-defined]
        r.empleado_legajo = emp.legajo if emp else None  # type: ignore[attr-defined]
        r.empleado_cuil = emp.cuil if emp else None  # type: ignore[attr-defined]
        r.empleado_fecha_nacimiento = emp.fecha_nacimiento if emp else None  # type: ignore[attr-defined]
        r.empleado_fecha_ingreso = emp.fecha_ingreso if emp else None  # type: ignore[attr-defined]
        r.empleado_area_nombre = area_map.get(emp.area_id) if emp and emp.area_id else None  # type: ignore[attr-defined]
        r.empleado_telefono = emp.telefono if emp else None  # type: ignore[attr-defined]
        r.tipo_licencia_nombre = tipo_map.get(r.tipo_licencia_id)  # type: ignore[attr-defined]
        r.creado_por_nombre = user_map.get(r.creado_por)  # type: ignore[attr-defined]
        r.validado_por_nombre = user_map.get(r.validado_por) if r.validado_por else None  # type: ignore[attr-defined]
