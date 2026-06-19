from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EvolucionCreate(BaseModel):
    atencion_id: UUID
    motivo_consulta: str
    anamnesis: str | None = None
    examen_fisico: str | None = None
    diagnostico_presuntivo: str | None = None
    diagnostico_definitivo: str | None = None
    tratamiento: str | None = None
    observaciones: str | None = None


class EvolucionUpdate(BaseModel):
    motivo_consulta: str | None = None
    anamnesis: str | None = None
    examen_fisico: str | None = None
    diagnostico_presuntivo: str | None = None
    diagnostico_definitivo: str | None = None
    tratamiento: str | None = None
    observaciones: str | None = None


class EvolucionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    atencion_id: UUID
    motivo_consulta: str
    anamnesis: str | None
    examen_fisico: str | None
    diagnostico_presuntivo: str | None
    diagnostico_definitivo: str | None
    tratamiento: str | None
    observaciones: str | None
    medico_id: UUID
    created_at: datetime
    updated_at: datetime
