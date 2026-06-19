from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.atenciones.models import Atencion, EstadoAtencion


async def insert(s: AsyncSession, a: Atencion) -> Atencion:
    s.add(a); await s.flush(); return a


async def get(s: AsyncSession, id_: UUID) -> Atencion | None:
    return (await s.execute(select(Atencion).where(Atencion.id == id_))).scalar_one_or_none()


async def list_(
    s: AsyncSession,
    *,
    empleado_id: UUID | None = None,
    medico_id: UUID | None = None,
    estado: EstadoAtencion | None = None,
    fecha: date | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Atencion]:
    stmt = select(Atencion).order_by(Atencion.fecha_turno.desc()).limit(limit).offset(offset)
    if empleado_id:
        stmt = stmt.where(Atencion.empleado_id == empleado_id)
    if medico_id:
        stmt = stmt.where(Atencion.medico_id == medico_id)
    if estado:
        stmt = stmt.where(Atencion.estado == estado)
    if fecha:
        from sqlalchemy import cast, Date
        stmt = stmt.where(cast(Atencion.fecha_turno, Date) == fecha)
    rows = list((await s.execute(stmt)).scalars())
    await _enrich(s, rows)
    return rows


async def get_enriched(s: AsyncSession, id_: UUID) -> Atencion | None:
    a = await get(s, id_)
    if a:
        await _enrich(s, [a])
    return a


async def update(s: AsyncSession, a: Atencion, **kwargs: object) -> Atencion:
    for k, v in kwargs.items():
        setattr(a, k, v)
    await s.flush()
    return a


async def _enrich(s: AsyncSession, rows: list[Atencion]) -> None:
    """Attach enriched display fields from related tables."""
    if not rows:
        return

    from app.modules.empleados.models import Empleado
    from app.modules.usuarios.models import Usuario

    emp_ids = {r.empleado_id for r in rows}
    medico_ids = {r.medico_id for r in rows if r.medico_id}

    # Empleados
    emp_map: dict[UUID, Empleado] = {}
    if emp_ids:
        result = await s.execute(select(Empleado).where(Empleado.id.in_(emp_ids)))
        for (emp,) in result:
            emp_map[emp.id] = emp

    # Medicos (usuarios)
    medico_map: dict[UUID, str] = {}
    if medico_ids:
        result = await s.execute(
            select(Usuario.id, Usuario.nombre, Usuario.email).where(Usuario.id.in_(medico_ids))
        )
        for uid, nombre, email in result:
            medico_map[uid] = nombre or email

    for r in rows:
        emp = emp_map.get(r.empleado_id)
        r.empleado_nombre = f"{emp.apellido}, {emp.nombre}" if emp else None  # type: ignore[attr-defined]
        r.empleado_legajo = emp.legajo if emp else None  # type: ignore[attr-defined]
        r.empleado_cuil = emp.cuil if emp else None  # type: ignore[attr-defined]
        r.medico_nombre = medico_map.get(r.medico_id) if r.medico_id else None  # type: ignore[attr-defined]
