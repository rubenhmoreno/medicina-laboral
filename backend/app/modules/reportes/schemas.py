from datetime import date
from pydantic import BaseModel


class AusentismoPorArea(BaseModel):
    area_id: str | None
    area_nombre: str | None
    total_licencias: int
    total_dias_otorgados: int


class AusentismoPorCategoriaDiag(BaseModel):
    categoria_diagnostico: str | None
    total_licencias: int
    total_dias_otorgados: int


class FrecuenciaMensual(BaseModel):
    anio: int
    mes: int
    total_licencias: int
    total_dias_otorgados: int


class ReporteParams(BaseModel):
    desde: date
    hasta: date
    area_id: str | None = None
