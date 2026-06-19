# backend/app/modules/usuarios/schemas.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.usuarios.models import Rol


class UsuarioCreate(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=128)
    nombre: str | None = None
    rol: Rol
    matricula: str | None = None


class UsuarioUpdate(BaseModel):
    nombre: str | None = None
    rol: Rol | None = None
    matricula: str | None = None
    activo: bool | None = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    nombre: str | None
    rol: Rol
    matricula: str | None
    activo: bool
    ultimo_login: datetime | None


class LoginIn(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
