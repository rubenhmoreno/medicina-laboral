from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class CategoriaLaboral(Base):
    __tablename__ = "categorias_laborales"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
