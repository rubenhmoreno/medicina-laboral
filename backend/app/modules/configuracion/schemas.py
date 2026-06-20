from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConfiguracionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clave: str
    valor: str
    descripcion: str | None = None


class ConfiguracionUpdate(BaseModel):
    valor: str
