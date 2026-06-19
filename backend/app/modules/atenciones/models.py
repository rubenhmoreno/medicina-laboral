from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class EstadoAtencion(StrEnum):
    PENDIENTE = "pendiente"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class Atencion(Base):
    __tablename__ = "atenciones"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    empleado_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("empleados.id"))
    asignado_por: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("usuarios.id"))
    medico_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    fecha_turno: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    motivo: Mapped[str] = mapped_column(Text)
    estado: Mapped[EstadoAtencion] = mapped_column(
        SAEnum(EstadoAtencion, name="estado_atencion",
               values_callable=lambda e: [v.value for v in e]),
        default=EstadoAtencion.PENDIENTE,
    )
    notas_medicas: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
