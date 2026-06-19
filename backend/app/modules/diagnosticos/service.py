from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.diagnosticos import repository as repo
from app.modules.diagnosticos.models import Diagnostico
from app.modules.diagnosticos.schemas import DiagnosticoCreate


async def create_diagnostico(s: AsyncSession, p: DiagnosticoCreate) -> Diagnostico:
    return await repo.insert(s, Diagnostico(
        codigo_cie10=p.codigo_cie10, descripcion=p.descripcion,
        categoria=p.categoria, requiere_junta=p.requiere_junta,
    ))
