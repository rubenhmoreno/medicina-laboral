"""Replace diagnostico_id FK with diagnostico text column.

Revision ID: d8a1e3f5b2c4
Revises: b5f2a7d9e1c3
Create Date: 2026-06-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d8a1e3f5b2c4"
down_revision = "b5f2a7d9e1c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add new text column to licencias
    op.add_column("licencias", sa.Column("diagnostico", sa.String(500), nullable=True))

    # 2. Copy descriptions from diagnosticos table into the new column
    op.execute("""
        UPDATE licencias l
        SET diagnostico = d.descripcion
        FROM diagnosticos d
        WHERE l.diagnostico_id = d.id
    """)

    # 3. Drop the FK constraint and column from licencias
    op.drop_constraint("licencias_diagnostico_id_fkey", "licencias", type_="foreignkey")
    op.drop_column("licencias", "diagnostico_id")

    # 4. Add diagnostico_definitivo text column to evoluciones
    op.add_column("evoluciones", sa.Column("diagnostico_definitivo", sa.String(500), nullable=True))

    # 5. Copy descriptions from diagnosticos table into evoluciones
    op.execute("""
        UPDATE evoluciones e
        SET diagnostico_definitivo = d.descripcion
        FROM diagnosticos d
        WHERE e.diagnostico_definitivo_id = d.id
    """)

    # 6. Drop FK and column from evoluciones
    op.drop_constraint("evoluciones_diagnostico_definitivo_id_fkey", "evoluciones", type_="foreignkey")
    op.drop_column("evoluciones", "diagnostico_definitivo_id")

    # 7. Drop the diagnosticos table
    op.drop_table("diagnosticos")


def downgrade() -> None:
    # Recreate diagnosticos table
    op.create_table(
        "diagnosticos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo_cie10", sa.String(20), nullable=True),
        sa.Column("descripcion", sa.String(500), nullable=False),
        sa.Column("categoria", sa.String(100), nullable=True),
        sa.Column("requiere_junta", sa.Boolean(), server_default="false"),
    )

    # Re-add FK column to licencias
    op.add_column(
        "licencias",
        sa.Column("diagnostico_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "licencias_diagnostico_id_fkey", "licencias", "diagnosticos",
        ["diagnostico_id"], ["id"],
    )
    op.drop_column("licencias", "diagnostico")

    # Re-add FK column to evoluciones
    op.add_column(
        "evoluciones",
        sa.Column("diagnostico_definitivo_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "evoluciones_diagnostico_definitivo_id_fkey", "evoluciones", "diagnosticos",
        ["diagnostico_definitivo_id"], ["id"],
    )
    op.drop_column("evoluciones", "diagnostico_definitivo")
