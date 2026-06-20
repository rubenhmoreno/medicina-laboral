from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


_CUIL_RE = r"^\d{2}-\d{8}-\d{1}$|^\d{11}$"


class EmpleadoCreate(BaseModel):
    legajo: str = Field(min_length=1, max_length=40, pattern=r"^\d+$")
    cuil: str = Field(pattern=_CUIL_RE)
    nombre: str
    apellido: str
    fecha_nacimiento: date | None = None
    fecha_ingreso: date
    area_id: UUID | None = None
    categoria_id: UUID
    supervisor_id: UUID | None = None
    obra_social: str | None = None
    nro_carnet: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None

    @field_validator("cuil")
    @classmethod
    def normalize_cuil(cls, v: str) -> str:
        return v.replace("-", "")


class EmpleadoUpdate(BaseModel):
    nombre: str | None = None
    apellido: str | None = None
    area_id: UUID | None = None
    categoria_id: UUID | None = None
    supervisor_id: UUID | None = None
    obra_social: str | None = None
    nro_carnet: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None
    activo: bool | None = None


class EmpleadoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    legajo: str
    cuil: str
    nombre: str
    apellido: str
    fecha_nacimiento: date | None
    fecha_ingreso: date
    area_id: UUID | None
    categoria_id: UUID
    supervisor_id: UUID | None
    obra_social: str | None
    nro_carnet: str | None
    email: str | None
    telefono: str | None
    activo: bool
