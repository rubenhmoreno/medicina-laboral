from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Diagnostico(Base):
    __tablename__ = "diagnosticos"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    codigo_cie10: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    descripcion: Mapped[str] = mapped_column(String(255))
    categoria: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)
    requiere_junta: Mapped[bool] = mapped_column(Boolean, default=False)
