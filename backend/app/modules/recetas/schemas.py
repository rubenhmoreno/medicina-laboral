from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemRecetaIn(BaseModel):
    medicamento: str
    dosis: str | None = None
    frecuencia: str | None = None
    duracion: str | None = None


class ItemRecetaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    medicamento: str
    dosis: str | None
    frecuencia: str | None
    duracion: str | None
    orden: int


class RecetaCreate(BaseModel):
    atencion_id: UUID
    diagnostico: str | None = None
    observaciones: str | None = None
    items: list[ItemRecetaIn] = []


class RecetaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    atencion_id: UUID
    medico_id: UUID
    diagnostico: str | None
    observaciones: str | None
    created_at: datetime
    items: list[ItemRecetaOut] = []
