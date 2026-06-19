from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemPedidoIn(BaseModel):
    descripcion: str
    codigo: str | None = None


class ItemPedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    descripcion: str
    codigo: str | None
    orden: int


class PedidoCreate(BaseModel):
    atencion_id: UUID
    tipo: str
    diagnostico: str | None = None
    indicaciones: str | None = None
    items: list[ItemPedidoIn] = []


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    atencion_id: UUID
    medico_id: UUID
    tipo: str
    diagnostico: str | None
    indicaciones: str | None
    created_at: datetime
    items: list[ItemPedidoOut] = []
