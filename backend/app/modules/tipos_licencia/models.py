from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class TipoLicencia(Base):
    __tablename__ = "tipos_licencia"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    base_legal: Mapped[str | None] = mapped_column(String(120), nullable=True)
    paga: Mapped[bool] = mapped_column(Boolean, default=True)
    computa_dias: Mapped[bool] = mapped_column(Boolean, default=True)
