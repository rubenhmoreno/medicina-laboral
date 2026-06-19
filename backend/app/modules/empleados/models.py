from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Empleado(Base):
    __tablename__ = "empleados"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    legajo: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    cuil: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    apellido: Mapped[str] = mapped_column(String(120))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    fecha_ingreso: Mapped[date] = mapped_column(Date)
    area_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("areas.id"), nullable=True)
    categoria_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("categorias_laborales.id"))
    supervisor_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("empleados.id"), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
