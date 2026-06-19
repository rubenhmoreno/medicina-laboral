from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auditoria.models import Auditoria


async def append(
    session: AsyncSession,
    *,
    accion: str,
    entidad: str,
    usuario_id: UUID | None,
    entidad_id: UUID | None,
    payload: dict[str, Any] | None,
    ip: str | None,
    user_agent: str | None,
) -> None:
    session.add(
        Auditoria(
            accion=accion,
            entidad=entidad,
            usuario_id=usuario_id,
            entidad_id=entidad_id,
            payload=payload,
            ip=ip,
            user_agent=user_agent,
        )
    )
    await session.flush()
