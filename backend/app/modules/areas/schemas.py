from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AreaCreate(BaseModel):
    nombre: str
    parent_id: UUID | None = None


class AreaUpdate(BaseModel):
    nombre: str | None = None
    parent_id: UUID | None = None


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    nombre: str
    parent_id: UUID | None
