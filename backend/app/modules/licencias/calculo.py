from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.empleados.models import Empleado
from app.modules.licencias.models import EstadoLicencia, Licencia
from app.modules.topes import repository as topes_repo


def calcular_dias(fecha_desde: date, fecha_hasta: date) -> int:
    if fecha_hasta < fecha_desde:
        raise ValueError("fecha_hasta < fecha_desde")
    return (fecha_hasta - fecha_desde).days + 1


def ventana_para(
    ventana: str, *, fecha_ingreso: date, fecha_ref: date
) -> tuple[date, date]:
    if ventana == "anio-calendario":
        return date(fecha_ref.year, 1, 1), date(fecha_ref.year, 12, 31)
    if ventana == "anio-aniversario":
        # Determine the current aniversario "year start" relative to fecha_ref.
        anios = fecha_ref.year - fecha_ingreso.year
        if (fecha_ref.month, fecha_ref.day) < (fecha_ingreso.month, fecha_ingreso.day):
            anios -= 1
        try:
            inicio = fecha_ingreso.replace(year=fecha_ingreso.year + anios)
        except ValueError:
            # 29-feb edge: fall back to 28-feb in non-leap years
            inicio = date(fecha_ingreso.year + anios, 2, 28)
        try:
            fin = inicio.replace(year=inicio.year + 1) - timedelta(days=1)
        except ValueError:
            fin = date(inicio.year + 1, 2, 28) - timedelta(days=1)
        return inicio, fin
    raise ValueError(f"ventana desconocida: {ventana}")


@dataclass(frozen=True)
class TopeEvaluacion:
    tope_aplicable: int | None
    dias_consumidos_ventana: int
    dias_restantes: int
    excede: bool
    warning_msg: str | None


async def dias_consumidos(
    s: AsyncSession,
    *,
    empleado_id: UUID,
    tipo_licencia_id: UUID,
    inicio: date,
    fin: date,
) -> int:
    stmt = (
        select(func.coalesce(func.sum(Licencia.dias_otorgados), 0))
        .where(
            and_(
                Licencia.empleado_id == empleado_id,
                Licencia.tipo_licencia_id == tipo_licencia_id,
                Licencia.estado == EstadoLicencia.VALIDADO,
                Licencia.fecha_desde >= inicio,
                Licencia.fecha_desde <= fin,
            )
        )
    )
    return int((await s.execute(stmt)).scalar_one() or 0)


async def evaluar_tope(
    s: AsyncSession,
    *,
    empleado: Empleado,
    tipo_licencia_id: UUID,
    dias_solicitados: int,
    fecha_ref: date,
) -> TopeEvaluacion:
    tope = await topes_repo.tope_vigente(
        s, categoria_id=empleado.categoria_id, tipo_licencia_id=tipo_licencia_id, en_fecha=fecha_ref
    )
    if tope is None or tope.ventana == "sin-limite":
        return TopeEvaluacion(None, 0, 0, False, None)

    inicio, fin = ventana_para(tope.ventana, fecha_ingreso=empleado.fecha_ingreso, fecha_ref=fecha_ref)
    consumidos = await dias_consumidos(
        s, empleado_id=empleado.id, tipo_licencia_id=tipo_licencia_id, inicio=inicio, fin=fin
    )
    excede = (consumidos + dias_solicitados) > tope.dias_maximos
    return TopeEvaluacion(
        tope_aplicable=tope.dias_maximos,
        dias_consumidos_ventana=consumidos,
        dias_restantes=max(0, tope.dias_maximos - consumidos),
        excede=excede,
        warning_msg=(
            f"Excede tope ({consumidos + dias_solicitados}/{tope.dias_maximos})" if excede else None
        ),
    )
