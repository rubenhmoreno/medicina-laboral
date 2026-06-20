from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class EstadoLicencia(StrEnum):
    BORRADOR = "borrador"
    ENVIADO = "enviado"
    VALIDADO = "validado"
    RECHAZADO = "rechazado"
    ANULADO = "anulado"


class OrigenLicencia(StrEnum):
    RRHH = "rrhh"
    MEDICO = "medico"


class Licencia(Base):
    __tablename__ = "licencias"
    __table_args__ = (
        CheckConstraint("dias_solicitados > 0", name="ck_dias_sol_positivo"),
        CheckConstraint("fecha_hasta >= fecha_desde", name="ck_rango_fechas"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    empleado_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("empleados.id"))
    tipo_licencia_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("tipos_licencia.id"))
    diagnostico: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fecha_desde: Mapped[date] = mapped_column(Date)
    fecha_hasta: Mapped[date] = mapped_column(Date)
    dias_solicitados: Mapped[int] = mapped_column(Integer)
    dias_otorgados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[EstadoLicencia] = mapped_column(SAEnum(EstadoLicencia, name="estado_licencia"))
    origen: Mapped[OrigenLicencia] = mapped_column(SAEnum(OrigenLicencia, name="origen_licencia"))
    observaciones: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    motivo_rechazo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    motivo_anulacion: Mapped[str | None] = mapped_column(String(500), nullable=True)
    certificante: Mapped[str | None] = mapped_column(String(255), nullable=True)
    matricula_certificante: Mapped[str | None] = mapped_column(String(40), nullable=True)
    creado_por: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("usuarios.id"))
    validado_por: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    validado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    modo_constatacion: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
