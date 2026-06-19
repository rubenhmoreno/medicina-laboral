from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.licencias import repository as repo
from app.modules.licencias.calculo import TopeEvaluacion
from app.modules.licencias.models import EstadoLicencia
from app.modules.licencias.schemas import (
    AnularIn, LicenciaCreate, LicenciaOut, RechazarIn, ValidarIn,
)
from app.modules.licencias.service import (
    anular, crear_licencia, enviar, evaluar_tope_para_licencia, rechazar, validar,
)
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/licencias", tags=["licencias"])


@router.get("", response_model=list[LicenciaOut])
async def list_(
    estado: EstadoLicencia | None = Query(default=None),
    empleado_id: UUID | None = Query(default=None),
    area_id: UUID | None = Query(default=None),
    desde: date | None = Query(default=None),
    hasta: date | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    s: AsyncSession = Depends(get_db),
    user: Usuario = Depends(current_user),
):
    rows = await repo.list_(s,
        estado=estado, empleado_id=empleado_id, area_id=area_id,
        desde=desde, hasta=hasta, limit=limit, offset=offset)
    # Hide sensitive fields for RRHH
    if user.rol == Rol.RRHH:
        for r in rows:
            r.diagnostico_id = None
            r.observaciones = None
            r.motivo_rechazo = None
    return rows


@router.get("/{id_}", response_model=LicenciaOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user)):
    lic = await repo.get(s, id_)
    if not lic:
        raise NotFoundError("licencia no encontrada")
    if user.rol == Rol.RRHH:
        lic.diagnostico_id = None
        lic.observaciones = None
        lic.motivo_rechazo = None
    return lic


@router.post("", response_model=LicenciaOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))])
async def create(
    payload: LicenciaCreate, s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user)
):
    return await crear_licencia(s, payload=payload, actor=user)


@router.post("/{id_}/enviar", response_model=LicenciaOut,
             dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))])
async def enviar_ep(id_: UUID, s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user)):
    return await enviar(s, lic_id=id_, actor=user)


@router.post("/{id_}/validar", response_model=LicenciaOut,
             dependencies=[Depends(require_role(Rol.MEDICO, Rol.ADMIN))])
async def validar_ep(
    id_: UUID, payload: ValidarIn,
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    return await validar(s, lic_id=id_, payload=payload, actor=user)


@router.post("/{id_}/rechazar", response_model=LicenciaOut,
             dependencies=[Depends(require_role(Rol.MEDICO, Rol.ADMIN))])
async def rechazar_ep(
    id_: UUID, payload: RechazarIn,
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    return await rechazar(s, lic_id=id_, payload=payload, actor=user)


@router.post("/{id_}/anular", response_model=LicenciaOut,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def anular_ep(
    id_: UUID, payload: AnularIn,
    s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user),
):
    return await anular(s, lic_id=id_, payload=payload, actor=user)


@router.get("/{id_}/tope")
async def tope_ep(id_: UUID, s: AsyncSession = Depends(get_db), user: Usuario = Depends(current_user)):
    ev: TopeEvaluacion = await evaluar_tope_para_licencia(s, id_)
    return ev.__dict__
