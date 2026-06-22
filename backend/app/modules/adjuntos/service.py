from uuid import UUID

from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import Settings
from app.core.storage import presigned_get, put_object, sha256_of
from app.modules.adjuntos import repository as repo
from app.modules.adjuntos.models import Adjunto
from app.shared.exceptions import NotFoundError, ValidationError

_ALLOWED_MIME = {"application/pdf", "image/png", "image/jpeg", "image/webp"}
_MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


async def upload_adjunto(
    s: AsyncSession,
    *,
    mc: Minio,
    settings: Settings,
    licencia_id: UUID | None = None,
    atencion_id: UUID | None = None,
    nombre_original: str,
    mime_type: str,
    payload: bytes,
    usuario_id: UUID | None,
) -> Adjunto:
    if not licencia_id and not atencion_id:
        raise ValidationError("debe indicar licencia_id o atencion_id")
    if licencia_id and atencion_id:
        raise ValidationError("debe indicar solo uno: licencia_id o atencion_id")
    if mime_type not in _ALLOWED_MIME:
        raise ValidationError("tipo de archivo no permitido", detail={"mime": mime_type})
    if len(payload) > _MAX_SIZE_BYTES:
        raise ValidationError("archivo demasiado grande", detail={"max": _MAX_SIZE_BYTES})

    digest = sha256_of(payload)
    if licencia_id:
        key = f"licencias/{licencia_id}/{digest}-{nombre_original}"
    else:
        key = f"atenciones/{atencion_id}/{digest}-{nombre_original}"
    put_object(mc, settings.minio_bucket, key, payload, mime_type)

    return await repo.insert(
        s,
        Adjunto(
            licencia_id=licencia_id,
            atencion_id=atencion_id,
            nombre_original=nombre_original,
            mime_type=mime_type,
            size_bytes=len(payload),
            sha256=digest,
            storage_key=key,
            subido_por=usuario_id,
        ),
    )


async def download_url(
    s: AsyncSession, mc: Minio, settings: Settings, adjunto_id: UUID
) -> tuple[str, int]:
    adj = await repo.get(s, adjunto_id)
    if not adj:
        raise NotFoundError("adjunto no encontrado")
    ttl_min = 5
    return presigned_get(mc, settings.minio_bucket, adj.storage_key, ttl_minutes=ttl_min), ttl_min * 60
