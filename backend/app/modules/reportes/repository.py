from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ausentismo_por_area(s: AsyncSession, desde: date, hasta: date) -> list[dict]:
    sql = text("""
        SELECT a.id::text AS area_id, a.nombre AS area_nombre,
               COUNT(l.id) AS total_licencias,
               COALESCE(SUM(l.dias_otorgados), 0) AS total_dias_otorgados
        FROM licencias l
        JOIN empleados e ON e.id = l.empleado_id
        LEFT JOIN areas a ON a.id = e.area_id
        WHERE l.estado = 'VALIDADO'::estado_licencia
          AND l.fecha_desde BETWEEN :desde AND :hasta
        GROUP BY a.id, a.nombre
        ORDER BY total_dias_otorgados DESC
    """)
    res = await s.execute(sql, {"desde": desde, "hasta": hasta})
    return [dict(r._mapping) for r in res]


async def ausentismo_por_categoria_diag(s: AsyncSession, desde: date, hasta: date) -> list[dict]:
    # Aggregates by DIAGNOSTIC CATEGORY only — never by description (PII).
    sql = text("""
        SELECT d.categoria AS categoria_diagnostico,
               COUNT(l.id) AS total_licencias,
               COALESCE(SUM(l.dias_otorgados), 0) AS total_dias_otorgados
        FROM licencias l
        LEFT JOIN diagnosticos d ON d.id = l.diagnostico_id
        WHERE l.estado = 'VALIDADO'::estado_licencia
          AND l.fecha_desde BETWEEN :desde AND :hasta
        GROUP BY d.categoria
        ORDER BY total_dias_otorgados DESC
    """)
    res = await s.execute(sql, {"desde": desde, "hasta": hasta})
    return [dict(r._mapping) for r in res]


async def frecuencia_mensual(s: AsyncSession, desde: date, hasta: date) -> list[dict]:
    sql = text("""
        SELECT EXTRACT(YEAR FROM l.fecha_desde)::int AS anio,
               EXTRACT(MONTH FROM l.fecha_desde)::int AS mes,
               COUNT(l.id) AS total_licencias,
               COALESCE(SUM(l.dias_otorgados), 0) AS total_dias_otorgados
        FROM licencias l
        WHERE l.estado = 'VALIDADO'::estado_licencia
          AND l.fecha_desde BETWEEN :desde AND :hasta
        GROUP BY 1, 2
        ORDER BY 1, 2
    """)
    res = await s.execute(sql, {"desde": desde, "hasta": hasta})
    return [dict(r._mapping) for r in res]
