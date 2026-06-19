from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AtencionCreate(BaseModel):
    empleado_id: UUID
    medico_id: UUID | None = None
    fecha_turno: datetime
    motivo: str


class AtencionUpdate(BaseModel):
    medico_id: UUID | None = None
    fecha_turno: datetime | None = None
    motivo: str | None = None


class CompletarIn(BaseModel):
    notas_medicas: str | None = None


class AtencionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    empleado_id: UUID
    asignado_por: UUID
    medico_id: UUID | None
    fecha_turno: datetime
    motivo: str
    estado: str
    notas_medicas: str | None
    created_at: datetime
    updated_at: datetime
    # Enriched fields
    empleado_nombre: str | None = None
    empleado_legajo: str | None = None
    empleado_cuil: str | None = None
    medico_nombre: str | None = None
