from enum import StrEnum
from uuid import UUID

from sqlalchemy import Boolean, Enum as SAEnum, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class TipoEstudio(StrEnum):
    LABORATORIO = "laboratorio"
    IMAGEN = "imagen"
    OTRO = "otro"


class EstudioCatalogo(Base):
    __tablename__ = "estudios_catalogo"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    nombre: Mapped[str] = mapped_column(String(255))
    codigo: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    tipo: Mapped[TipoEstudio] = mapped_column(
        SAEnum(TipoEstudio, name="tipo_estudio",
               values_callable=lambda e: [v.value for v in e])
    )
    categoria: Mapped[str | None] = mapped_column(String(100), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
