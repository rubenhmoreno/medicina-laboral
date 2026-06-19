from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import current_user, get_db
from app.core.permissions import require_role
from app.core.settings import Settings, get_settings
from app.core.storage import minio_client
from app.modules.adjuntos.schemas import AdjuntoDownload, AdjuntoOut
from app.modules.adjuntos.service import download_url, upload_adjunto
from app.modules.usuarios.models import Rol, Usuario

router = APIRouter(prefix="/api/adjuntos", tags=["adjuntos"])


def _mc(settings: Settings = Depends(get_settings)) -> Minio:
    return minio_client(settings)


@router.post("", response_model=AdjuntoOut, status_code=201,
             dependencies=[Depends(require_role(Rol.ADMIN, Rol.RRHH, Rol.MEDICO))])
async def upload(
    licencia_id: UUID = Form(...),
    file: UploadFile = File(...),
    s: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    mc: Minio = Depends(_mc),
    user: Usuario = Depends(current_user),
):
    payload = await file.read()
    return await upload_adjunto(
        s, mc=mc, settings=settings, licencia_id=licencia_id,
        nombre_original=file.filename or "archivo",
        mime_type=file.content_type or "application/octet-stream",
        payload=payload, usuario_id=user.id,
    )


@router.get("/{id_}/download", response_model=AdjuntoDownload)
async def get_download(
    id_: UUID,
    s: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    mc: Minio = Depends(_mc),
    user: Usuario = Depends(current_user),
):
    url, ttl = await download_url(s, mc, settings, id_)
    return AdjuntoDownload(url=url, expires_in_seconds=ttl)
