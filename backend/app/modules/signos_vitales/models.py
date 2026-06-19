from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class SignosVitales(Base):
    __tablename__ = "signos_vitales"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    atencion_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("atenciones.id"), unique=True)
    peso_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    altura_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    imc: Mapped[float | None] = mapped_column(Float, nullable=True)
    presion_sistolica: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    presion_diastolica: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    temperatura: Mapped[float | None] = mapped_column(Float, nullable=True)
    frecuencia_cardiaca: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    saturacion_o2: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    glucemia: Mapped[float | None] = mapped_column(Float, nullable=True)
    registrado_por: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("usuarios.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
