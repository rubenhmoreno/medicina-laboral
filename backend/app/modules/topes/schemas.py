from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TopeSet(BaseModel):
    dias_maximos: int = Field(ge=0)
    ventana: str  # validated by CHECK
    desde: date
    observacion: str | None = None


class TopeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    categoria_id: UUID
    tipo_licencia_id: UUID
    dias_maximos: int
    ventana: str
    vigente_desde: date
    vigente_hasta: date | None
    observacion: str | None
