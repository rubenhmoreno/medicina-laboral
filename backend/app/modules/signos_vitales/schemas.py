from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class SignosVitalesCreate(BaseModel):
    atencion_id: UUID
    peso_kg: float | None = None
    altura_cm: float | None = None
    presion_sistolica: int | None = None
    presion_diastolica: int | None = None
    temperatura: float | None = None
    frecuencia_cardiaca: int | None = None
    saturacion_o2: int | None = None
    glucemia: float | None = None


class SignosVitalesUpdate(BaseModel):
    peso_kg: float | None = None
    altura_cm: float | None = None
    presion_sistolica: int | None = None
    presion_diastolica: int | None = None
    temperatura: float | None = None
    frecuencia_cardiaca: int | None = None
    saturacion_o2: int | None = None
    glucemia: float | None = None


class SignosVitalesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    atencion_id: UUID
    peso_kg: float | None
    altura_cm: float | None
    imc: float | None
    presion_sistolica: int | None
    presion_diastolica: int | None
    temperatura: float | None
    frecuencia_cardiaca: int | None
    saturacion_o2: int | None
    glucemia: float | None
    registrado_por: UUID
    created_at: datetime
    updated_at: datetime
