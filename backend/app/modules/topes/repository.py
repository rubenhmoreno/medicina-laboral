from datetime import date
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.topes.models import TopeDias


async def tope_vigente(
    s: AsyncSession, categoria_id: UUID, tipo_licencia_id: UUID, en_fecha: date
) -> TopeDias | None:
    stmt = (
        select(TopeDias)
        .where(
            TopeDias.categoria_id == categoria_id,
            TopeDias.tipo_licencia_id == tipo_licencia_id,
            TopeDias.vigente_desde <= en_fecha,
            (TopeDias.vigente_hasta.is_(None)) | (TopeDias.vigente_hasta >= en_fecha),
        )
        .order_by(TopeDias.vigente_desde.desc())
        .limit(1)
    )
    return (await s.execute(stmt)).scalar_one_or_none()


async def set_tope(
    s: AsyncSession,
    *,
    categoria_id: UUID,
    tipo_licencia_id: UUID,
    dias_maximos: int,
    ventana: str,
    desde: date,
    observacion: str | None,
) -> TopeDias:
    # Close currently-open versions on the day before `desde`.
    await s.execute(
        update(TopeDias)
        .where(
            and_(
                TopeDias.categoria_id == categoria_id,
                TopeDias.tipo_licencia_id == tipo_licencia_id,
                TopeDias.vigente_hasta.is_(None),
            )
        )
        .values(vigente_hasta=desde)
    )
    nuevo = TopeDias(
        categoria_id=categoria_id,
        tipo_licencia_id=tipo_licencia_id,
        dias_maximos=dias_maximos,
        ventana=ventana,
        vigente_desde=desde,
        observacion=observacion,
    )
    s.add(nuevo)
    await s.flush()
    return nuevo


async def listar_actuales(s: AsyncSession) -> list[TopeDias]:
    stmt = select(TopeDias).where(TopeDias.vigente_hasta.is_(None))
    return list((await s.execute(stmt)).scalars())
