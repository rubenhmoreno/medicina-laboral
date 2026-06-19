from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EstudioCatalogoCreate(BaseModel):
    nombre: str
    codigo: str | None = None
    tipo: str
    categoria: str | None = None
    activo: bool = True


class EstudioCatalogoUpdate(BaseModel):
    nombre: str | None = None
    codigo: str | None = None
    tipo: str | None = None
    categoria: str | None = None
    activo: bool | None = None


class EstudioCatalogoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    nombre: str
    codigo: str | None
    tipo: str
    categoria: str | None
    activo: bool
