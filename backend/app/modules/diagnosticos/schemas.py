from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DiagnosticoCreate(BaseModel):
    codigo_cie10: str | None = None
    descripcion: str
    categoria: str | None = None
    requiere_junta: bool = False


class DiagnosticoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    codigo_cie10: str | None
    descripcion: str
    categoria: str | None
    requiere_junta: bool
