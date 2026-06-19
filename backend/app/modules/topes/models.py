from datetime import date
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class TopeDias(Base):
    __tablename__ = "topes_dias"
    __table_args__ = (
        UniqueConstraint("categoria_id", "tipo_licencia_id", "vigente_desde", name="uq_tope_inicio"),
        CheckConstraint("ventana IN ('anio-calendario','anio-aniversario','sin-limite')", name="ck_ventana"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    categoria_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("categorias_laborales.id"))
    tipo_licencia_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("tipos_licencia.id"))
    dias_maximos: Mapped[int] = mapped_column(Integer)
    ventana: Mapped[str] = mapped_column(String(32))
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    observacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
