from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CategoriaCreate(BaseModel):
    codigo: str
    nombre: str


class CategoriaUpdate(BaseModel):
    codigo: str | None = None
    nombre: str | None = None
    activa: bool | None = None


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    codigo: str
    nombre: str
    activa: bool
