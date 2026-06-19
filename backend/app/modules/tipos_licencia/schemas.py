from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TipoLicenciaCreate(BaseModel):
    codigo: str
    nombre: str
    base_legal: str | None = None
    paga: bool = True
    computa_dias: bool = True


class TipoLicenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    codigo: str
    nombre: str
    base_legal: str | None
    paga: bool
    computa_dias: bool
