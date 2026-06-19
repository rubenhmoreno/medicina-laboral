from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.tipos_licencia import repository as repo
from app.modules.tipos_licencia.models import TipoLicencia
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.shared.exceptions import ConflictError


async def create_tipo(s: AsyncSession, p: TipoLicenciaCreate) -> TipoLicencia:
    if await repo.by_codigo(s, p.codigo):
        raise ConflictError("tipo de licencia ya existe", detail={"field": "codigo"})
    return await repo.insert(s, TipoLicencia(
        codigo=p.codigo, nombre=p.nombre, base_legal=p.base_legal,
        paga=p.paga, computa_dias=p.computa_dias,
    ))
