from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.modules.empleados import repository as repo
from app.modules.empleados.historia_clinica import HistoriaClinicaOut, build_historia_clinica
from app.modules.empleados.schemas import EmpleadoCreate, EmpleadoOut, EmpleadoUpdate
from app.modules.empleados.service import create_empleado, update_empleado
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import NotFoundError

router = APIRouter(prefix="/api/empleados", tags=["empleados"])


@router.get("", response_model=list[EmpleadoOut])
async def list_empleados(
    q: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    s: AsyncSession = Depends(get_db),
):
    return await repo.list_(s, q=q, limit=limit, offset=offset)


@router.get("/count")
async def count_empleados(s: AsyncSession = Depends(get_db)):
    total = await repo.count(s)
    return {"count": total}


@router.get("/{id_}", response_model=EmpleadoOut)
async def get_one(id_: UUID, s: AsyncSession = Depends(get_db)):
    e = await repo.get(s, id_)
    if not e:
        raise NotFoundError("empleado no encontrado")
    return e


@router.post(
    "", response_model=EmpleadoOut, status_code=201,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))],
)
async def create(payload: EmpleadoCreate, s: AsyncSession = Depends(get_db)):
    return await create_empleado(s, payload)


@router.put(
    "/{id_}", response_model=EmpleadoOut,
    dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))],
)
async def update(id_: UUID, payload: EmpleadoUpdate, s: AsyncSession = Depends(get_db)):
    return await update_empleado(s, id_, payload)


@router.get("/{id_}/historia-clinica", response_model=HistoriaClinicaOut)
async def historia_clinica(
    id_: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    return await build_historia_clinica(s, id_)


@router.get("/{id_}/historia-clinica/pdf")
async def historia_clinica_pdf(
    id_: UUID,
    s: AsyncSession = Depends(get_db),
    _user: Usuario = Depends(current_user),
):
    from app.modules.configuracion.repository import get_dict as config_get_dict
    from app.modules.empleados.pdf_historia import generate_pdf

    hc = await build_historia_clinica(s, id_)
    config = await config_get_dict(s)
    pdf_bytes = generate_pdf(hc, config=config)
    legajo = hc.empleado.legajo
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="historia_clinica_{legajo}.pdf"'},
    )
