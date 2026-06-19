import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.modules.auditoria import repository as audit_repo
from app.modules.reportes import service as svc
from app.modules.usuarios.models import Usuario

router = APIRouter(prefix="/api/reportes", tags=["reportes"])


def _csv_response(rows: list[dict], filename: str) -> StreamingResponse:
    buf = io.StringIO()
    if rows:
        writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/por-area")
async def por_area(
    desde: date = Query(...),
    hasta: date = Query(...),
    formato: str = Query("json", pattern="^(json|csv)$"),
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    rows = await svc.por_area(s, desde, hasta)
    if formato == "csv":
        await audit_repo.append(s, accion="export", entidad="reporte",
                                usuario_id=user.id, entidad_id=None,
                                payload={"reporte": "por_area", "desde": str(desde), "hasta": str(hasta)},
                                ip=None, user_agent=None)
        return _csv_response(rows, f"ausentismo_area_{desde}_{hasta}.csv")
    return rows


@router.get("/por-categoria-diag")
async def por_categoria_diag(
    desde: date = Query(...), hasta: date = Query(...),
    formato: str = Query("json", pattern="^(json|csv)$"),
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    rows = await svc.por_categoria_diag(s, desde, hasta)
    if formato == "csv":
        await audit_repo.append(s, accion="export", entidad="reporte",
                                usuario_id=user.id, entidad_id=None,
                                payload={"reporte": "por_categoria_diag"},
                                ip=None, user_agent=None)
        return _csv_response(rows, f"ausentismo_diag_{desde}_{hasta}.csv")
    return rows


@router.get("/mensual")
async def mensual(
    desde: date = Query(...), hasta: date = Query(...),
    formato: str = Query("json", pattern="^(json|csv)$"),
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    rows = await svc.por_mes(s, desde, hasta)
    if formato == "csv":
        await audit_repo.append(s, accion="export", entidad="reporte",
                                usuario_id=user.id, entidad_id=None,
                                payload={"reporte": "mensual"},
                                ip=None, user_agent=None)
        return _csv_response(rows, f"ausentismo_mensual_{desde}_{hasta}.csv")
    return rows
