from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db_base import Base
from app.core.ids import new_uuid7


class TipoPedido(StrEnum):
    LABORATORIO = "laboratorio"
    IMAGEN = "imagen"
    INTERCONSULTA = "interconsulta"
    OTRO = "otro"


class Pedido(Base):
    __tablename__ = "pedidos"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    atencion_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("atenciones.id"))
    medico_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("usuarios.id"))
    tipo: Mapped[TipoPedido] = mapped_column(
        SAEnum(TipoPedido, name="tipo_pedido",
               values_callable=lambda e: [v.value for v in e])
    )
    diagnostico: Mapped[str | None] = mapped_column(Text, nullable=True)
    indicaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", order_by="ItemPedido.orden"
    )


class ItemPedido(Base):
    __tablename__ = "items_pedido"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    pedido_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("pedidos.id", ondelete="CASCADE"))
    descripcion: Mapped[str] = mapped_column(String(255))
    codigo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, default=0)

    pedido: Mapped["Pedido"] = relationship(back_populates="items")
