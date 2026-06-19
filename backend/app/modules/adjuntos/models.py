from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db_base import Base
from app.core.ids import new_uuid7


class Adjunto(Base):
    __tablename__ = "adjuntos"
    __table_args__ = (
        CheckConstraint(
            "(licencia_id IS NOT NULL AND atencion_id IS NULL) OR "
            "(licencia_id IS NULL AND atencion_id IS NOT NULL)",
            name="ck_adjunto_owner",
        ),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=new_uuid7)
    licencia_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("licencias.id", ondelete="CASCADE"), nullable=True
    )
    atencion_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("atenciones.id", ondelete="CASCADE"), nullable=True
    )
    nombre_original: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(255))
    subido_por: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
