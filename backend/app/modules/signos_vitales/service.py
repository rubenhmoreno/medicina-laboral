from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.signos_vitales import repository as repo
from app.modules.signos_vitales.models import SignosVitales
from app.modules.signos_vitales.schemas import SignosVitalesCreate, SignosVitalesUpdate
from app.modules.atenciones import repository as aten_repo
from app.shared.exceptions import ConflictError, NotFoundError


def _calc_imc(peso_kg: float | None, altura_cm: float | None) -> float | None:
    if peso_kg and altura_cm and altura_cm > 0:
        altura_m = altura_cm / 100
        return round(peso_kg / (altura_m * altura_m), 2)
    return None


async def create_signos(s: AsyncSession, payload: SignosVitalesCreate, actor_id: UUID) -> SignosVitales:
    if not await aten_repo.get(s, payload.atencion_id):
        raise NotFoundError("atencion no encontrada")
    if await repo.get_by_atencion(s, payload.atencion_id):
        raise ConflictError("ya existen signos vitales para esta atencion")
    imc = _calc_imc(payload.peso_kg, payload.altura_cm)
    return await repo.insert(s, SignosVitales(
        atencion_id=payload.atencion_id,
        peso_kg=payload.peso_kg,
        altura_cm=payload.altura_cm,
        imc=imc,
        presion_sistolica=payload.presion_sistolica,
        presion_diastolica=payload.presion_diastolica,
        temperatura=payload.temperatura,
        frecuencia_cardiaca=payload.frecuencia_cardiaca,
        saturacion_o2=payload.saturacion_o2,
        glucemia=payload.glucemia,
        registrado_por=actor_id,
    ))


async def update_signos(s: AsyncSession, id_: UUID, payload: SignosVitalesUpdate) -> SignosVitales:
    sv = await repo.get(s, id_)
    if not sv:
        raise NotFoundError("signos vitales no encontrados")
    updates = payload.model_dump(exclude_unset=True)
    # Recalculate IMC if weight or height changed
    peso = updates.get("peso_kg", sv.peso_kg)
    altura = updates.get("altura_cm", sv.altura_cm)
    updates["imc"] = _calc_imc(peso, altura)
    return await repo.update(s, sv, **updates)
