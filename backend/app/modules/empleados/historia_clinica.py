from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.adjuntos.schemas import AdjuntoOut
from app.modules.atenciones.schemas import AtencionOut
from app.modules.empleados.schemas import EmpleadoOut
from app.modules.evoluciones.schemas import EvolucionOut
from app.modules.licencias.schemas import LicenciaOut
from app.modules.pedidos.schemas import PedidoOut
from app.modules.recetas.schemas import RecetaOut
from app.modules.signos_vitales.schemas import SignosVitalesOut


# --- Schemas ---

class AtencionConDetalles(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    atencion: AtencionOut
    signos_vitales: SignosVitalesOut | None = None
    evoluciones: list[EvolucionOut] = []
    recetas: list[RecetaOut] = []
    pedidos: list[PedidoOut] = []


class HistoriaClinicaOut(BaseModel):
    empleado: EmpleadoOut
    licencias: list[LicenciaOut] = []
    atenciones: list[AtencionConDetalles] = []
    adjuntos: list[AdjuntoOut] = []


# --- Service ---

async def build_historia_clinica(s: AsyncSession, empleado_id: UUID) -> HistoriaClinicaOut:
    from app.modules.empleados import repository as emp_repo
    from app.modules.licencias import repository as lic_repo
    from app.modules.atenciones import repository as aten_repo
    from app.modules.signos_vitales import repository as sv_repo
    from app.modules.evoluciones import repository as ev_repo
    from app.modules.recetas import repository as rec_repo
    from app.modules.pedidos import repository as ped_repo
    from app.modules.adjuntos import repository as adj_repo
    from app.shared.exceptions import NotFoundError

    emp = await emp_repo.get(s, empleado_id)
    if not emp:
        raise NotFoundError("empleado no encontrado")

    licencias = await lic_repo.list_(s, empleado_id=empleado_id, limit=500)

    atenciones_raw = await aten_repo.list_(s, empleado_id=empleado_id, limit=500)

    atenciones_detalle: list[AtencionConDetalles] = []
    for a in atenciones_raw:
        sv = await sv_repo.get_by_atencion(s, a.id)
        evols = await ev_repo.list_by_atencion(s, a.id)
        recetas = await rec_repo.list_by_atencion(s, a.id)
        pedidos = await ped_repo.list_by_atencion(s, a.id)
        atenciones_detalle.append(AtencionConDetalles(
            atencion=AtencionOut.model_validate(a),
            signos_vitales=SignosVitalesOut.model_validate(sv) if sv else None,
            evoluciones=[EvolucionOut.model_validate(e) for e in evols],
            recetas=[RecetaOut.model_validate(r) for r in recetas],
            pedidos=[PedidoOut.model_validate(p) for p in pedidos],
        ))

    # Collect all adjuntos: from licencias + atenciones
    from sqlalchemy import select, or_
    from app.modules.adjuntos.models import Adjunto

    lic_ids = [l.id for l in licencias]
    aten_ids = [a.id for a in atenciones_raw]
    conds = []
    if lic_ids:
        conds.append(Adjunto.licencia_id.in_(lic_ids))
    if aten_ids:
        conds.append(Adjunto.atencion_id.in_(aten_ids))

    adjuntos_all: list[Adjunto] = []
    if conds:
        stmt = select(Adjunto).where(or_(*conds)).order_by(Adjunto.created_at)
        adjuntos_all = list((await s.execute(stmt)).scalars())

    return HistoriaClinicaOut(
        empleado=EmpleadoOut.model_validate(emp),
        licencias=[LicenciaOut.model_validate(l) for l in licencias],
        atenciones=atenciones_detalle,
        adjuntos=[AdjuntoOut.model_validate(a) for a in adjuntos_all],
    )
