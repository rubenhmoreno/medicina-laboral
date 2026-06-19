from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Evolucion(Base):
    __tablename__ = "evoluciones"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    atencion_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("atenciones.id"))
    motivo_consulta: Mapped[str] = mapped_column(Text)
    anamnesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    examen_fisico: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostico_presuntivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnostico_definitivo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tratamiento: Mapped[str | None] = mapped_column(Text, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    medico_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("usuarios.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
