from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.topes import repository as repo
from app.modules.topes.models import TopeDias
from app.modules.topes.schemas import TopeSet
from app.shared.exceptions import ValidationError


_VENTANAS = {"anio-calendario", "anio-aniversario", "sin-limite"}


async def set_tope(
    s: AsyncSession,
    categoria_id: UUID,
    tipo_licencia_id: UUID,
    payload: TopeSet,
) -> TopeDias:
    if payload.ventana not in _VENTANAS:
        raise ValidationError("ventana invalida", detail={"ventana": payload.ventana})
    return await repo.set_tope(
        s,
        categoria_id=categoria_id,
        tipo_licencia_id=tipo_licencia_id,
        dias_maximos=payload.dias_maximos,
        ventana=payload.ventana,
        desde=payload.desde,
        observacion=payload.observacion,
    )
