from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Configuracion(Base):
    __tablename__ = "configuracion"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    clave: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    valor: Mapped[str] = mapped_column(Text, default="")
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
