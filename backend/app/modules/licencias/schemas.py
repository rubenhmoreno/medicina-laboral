from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.licencias.models import EstadoLicencia, OrigenLicencia


class LicenciaCreate(BaseModel):
    empleado_id: UUID
    tipo_licencia_id: UUID
    diagnostico: str | None = None
    fecha_desde: date
    fecha_hasta: date
    observaciones: str | None = None
    certificante: str | None = None
    matricula_certificante: str | None = None

    @field_validator("fecha_hasta")
    @classmethod
    def rango_ok(cls, v: date, info):
        desde: date | None = info.data.get("fecha_desde")
        if desde and v < desde:
            raise ValueError("fecha_hasta debe ser >= fecha_desde")
        return v


class LicenciaUpdate(BaseModel):
    diagnostico: str | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    observaciones: str | None = None
    certificante: str | None = None
    matricula_certificante: str | None = None


class LicenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    empleado_id: UUID
    tipo_licencia_id: UUID
    diagnostico: str | None
    fecha_desde: date
    fecha_hasta: date
    dias_solicitados: int
    dias_otorgados: int | None
    estado: EstadoLicencia
    origen: OrigenLicencia
    observaciones: str | None
    motivo_rechazo: str | None
    motivo_anulacion: str | None
    certificante: str | None
    matricula_certificante: str | None
    creado_por: UUID
    validado_por: UUID | None
    validado_en: datetime | None
    # Enriched fields
    empleado_nombre: str | None = None
    empleado_legajo: str | None = None
    empleado_cuil: str | None = None
    empleado_fecha_nacimiento: date | None = None
    empleado_fecha_ingreso: date | None = None
    empleado_area_nombre: str | None = None
    tipo_licencia_nombre: str | None = None
    creado_por_nombre: str | None = None
    validado_por_nombre: str | None = None


class ValidarIn(BaseModel):
    dias_otorgados: int = Field(ge=0)
    observaciones: str | None = None


class RechazarIn(BaseModel):
    motivo_rechazo: str = Field(min_length=3, max_length=500)


class AnularIn(BaseModel):
    motivo_anulacion: str = Field(min_length=3, max_length=500)
