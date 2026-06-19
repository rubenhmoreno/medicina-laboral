from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.core.permissions import require_role
from app.modules.diagnosticos import repository as repo
from app.modules.diagnosticos.schemas import DiagnosticoCreate, DiagnosticoOut
from app.modules.diagnosticos.service import create_diagnostico
from app.modules.usuarios.models import Rol

router = APIRouter(prefix="/api/diagnosticos", tags=["diagnosticos"])


@router.get("", response_model=list[DiagnosticoOut])
async def list_(categoria: str | None = Query(default=None), s: AsyncSession = Depends(get_db)):
    return await repo.list_all(s, categoria=categoria)


@router.post("", response_model=DiagnosticoOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN))])
async def create(p: DiagnosticoCreate, s: AsyncSession = Depends(get_db)):
    return await create_diagnostico(s, p)
