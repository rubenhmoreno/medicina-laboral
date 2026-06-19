from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Receta(Base):
    __tablename__ = "recetas"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    atencion_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("atenciones.id"))
    medico_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("usuarios.id"))
    diagnostico: Mapped[str | None] = mapped_column(Text, nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["ItemReceta"]] = relationship(
        back_populates="receta", cascade="all, delete-orphan", order_by="ItemReceta.orden"
    )


class ItemReceta(Base):
    __tablename__ = "items_receta"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    receta_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("recetas.id", ondelete="CASCADE"))
    medicamento: Mapped[str] = mapped_column(String(255))
    dosis: Mapped[str | None] = mapped_column(String(255), nullable=True)
    frecuencia: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duracion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    receta: Mapped["Receta"] = relationship(back_populates="items")
