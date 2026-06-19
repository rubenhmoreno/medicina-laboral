from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tipos_licencia import repository as repo
from app.modules.tipos_licencia.models import TipoLicencia
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate, TipoLicenciaUpdate
from app.shared.exceptions import ConflictError, NotFoundError


async def create_tipo(s: AsyncSession, p: TipoLicenciaCreate) -> TipoLicencia:
    if await repo.by_codigo(s, p.codigo):
        raise ConflictError("tipo de licencia ya existe", detail={"field": "codigo"})
    return await repo.insert(s, TipoLicencia(
        codigo=p.codigo, nombre=p.nombre, base_legal=p.base_legal,
        paga=p.paga, computa_dias=p.computa_dias,
    ))


async def update_tipo(s: AsyncSession, id_: UUID, p: TipoLicenciaUpdate) -> TipoLicencia:
    tl = await repo.get(s, id_)
    if not tl:
        raise NotFoundError("tipo de licencia no encontrado")
    updates = p.model_dump(exclude_unset=True)
    if "codigo" in updates and updates["codigo"] != tl.codigo:
        if await repo.by_codigo(s, updates["codigo"]):
            raise ConflictError("codigo en uso", detail={"field": "codigo"})
    return await repo.update(s, tl, **updates)


async def delete_tipo(s: AsyncSession, id_: UUID) -> None:
    tl = await repo.get(s, id_)
    if not tl:
        raise NotFoundError("tipo de licencia no encontrado")
    from sqlalchemy import select, func
    from app.modules.licencias.models import Licencia
    count = (await s.execute(
        select(func.count()).where(Licencia.tipo_licencia_id == id_)
    )).scalar_one()
    if count > 0:
        raise ConflictError("tipo de licencia tiene licencias asociadas", detail={"licencias": count})
    await repo.delete(s, tl)
