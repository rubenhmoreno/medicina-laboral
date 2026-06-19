"""atenciones + clinical features: signos_vitales, evoluciones, recetas, pedidos, estudios_catalogo

Revision ID: b5f2a7d9e1c3
Revises: 142ccb53835a
Create Date: 2026-06-19 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b5f2a7d9e1c3'
down_revision: Union[str, Sequence[str], None] = '142ccb53835a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Use postgresql.ENUM with create_type=False to reference existing types
# without triggering auto-creation via the event hook.
estado_atencion_t = postgresql.ENUM('pendiente', 'completada', 'cancelada',
                                     name='estado_atencion', create_type=False)
tipo_estudio_t = postgresql.ENUM('laboratorio', 'imagen', 'otro',
                                  name='tipo_estudio', create_type=False)
tipo_pedido_t = postgresql.ENUM('laboratorio', 'imagen', 'interconsulta', 'otro',
                                 name='tipo_pedido', create_type=False)


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # Create enums via raw SQL with IF NOT EXISTS semantics
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE estado_atencion AS ENUM ('pendiente', 'completada', 'cancelada'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE tipo_estudio AS ENUM ('laboratorio', 'imagen', 'otro'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))
    conn.execute(sa.text(
        "DO $$ BEGIN "
        "  CREATE TYPE tipo_pedido AS ENUM ('laboratorio', 'imagen', 'interconsulta', 'otro'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$"
    ))

    # --- atenciones ---
    op.create_table('atenciones',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('empleado_id', sa.UUID(), nullable=False),
        sa.Column('asignado_por', sa.UUID(), nullable=False),
        sa.Column('medico_id', sa.UUID(), nullable=True),
        sa.Column('fecha_turno', sa.DateTime(timezone=True), nullable=False),
        sa.Column('motivo', sa.Text(), nullable=False),
        sa.Column('estado', estado_atencion_t, nullable=False),
        sa.Column('notas_medicas', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['empleado_id'], ['empleados.id']),
        sa.ForeignKeyConstraint(['asignado_por'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['medico_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # Alter adjuntos: make licencia_id nullable and add atencion_id
    op.alter_column('adjuntos', 'licencia_id', existing_type=sa.UUID(), nullable=True)
    op.add_column('adjuntos', sa.Column('atencion_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_adjuntos_atencion_id', 'adjuntos', 'atenciones',
                          ['atencion_id'], ['id'], ondelete='CASCADE')
    op.create_check_constraint(
        'ck_adjunto_owner', 'adjuntos',
        "(licencia_id IS NOT NULL AND atencion_id IS NULL) OR "
        "(licencia_id IS NULL AND atencion_id IS NOT NULL)"
    )

    # --- signos_vitales ---
    op.create_table('signos_vitales',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('atencion_id', sa.UUID(), nullable=False),
        sa.Column('peso_kg', sa.Float(), nullable=True),
        sa.Column('altura_cm', sa.Float(), nullable=True),
        sa.Column('imc', sa.Float(), nullable=True),
        sa.Column('presion_sistolica', sa.SmallInteger(), nullable=True),
        sa.Column('presion_diastolica', sa.SmallInteger(), nullable=True),
        sa.Column('temperatura', sa.Float(), nullable=True),
        sa.Column('frecuencia_cardiaca', sa.SmallInteger(), nullable=True),
        sa.Column('saturacion_o2', sa.SmallInteger(), nullable=True),
        sa.Column('glucemia', sa.Float(), nullable=True),
        sa.Column('registrado_por', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['atencion_id'], ['atenciones.id']),
        sa.ForeignKeyConstraint(['registrado_por'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('atencion_id'),
    )

    # --- evoluciones ---
    op.create_table('evoluciones',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('atencion_id', sa.UUID(), nullable=False),
        sa.Column('motivo_consulta', sa.Text(), nullable=False),
        sa.Column('anamnesis', sa.Text(), nullable=True),
        sa.Column('examen_fisico', sa.Text(), nullable=True),
        sa.Column('diagnostico_presuntivo', sa.Text(), nullable=True),
        sa.Column('diagnostico_definitivo_id', sa.UUID(), nullable=True),
        sa.Column('tratamiento', sa.Text(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('medico_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['atencion_id'], ['atenciones.id']),
        sa.ForeignKeyConstraint(['diagnostico_definitivo_id'], ['diagnosticos.id']),
        sa.ForeignKeyConstraint(['medico_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- recetas ---
    op.create_table('recetas',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('atencion_id', sa.UUID(), nullable=False),
        sa.Column('medico_id', sa.UUID(), nullable=False),
        sa.Column('diagnostico', sa.Text(), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['atencion_id'], ['atenciones.id']),
        sa.ForeignKeyConstraint(['medico_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- items_receta ---
    op.create_table('items_receta',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('receta_id', sa.UUID(), nullable=False),
        sa.Column('medicamento', sa.String(length=255), nullable=False),
        sa.Column('dosis', sa.String(length=255), nullable=True),
        sa.Column('frecuencia', sa.String(length=255), nullable=True),
        sa.Column('duracion', sa.String(length=255), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['receta_id'], ['recetas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- estudios_catalogo ---
    op.create_table('estudios_catalogo',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=True),
        sa.Column('tipo', tipo_estudio_t, nullable=False),
        sa.Column('categoria', sa.String(length=100), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_estudios_catalogo_codigo', 'estudios_catalogo', ['codigo'])

    # --- pedidos ---
    op.create_table('pedidos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('atencion_id', sa.UUID(), nullable=False),
        sa.Column('medico_id', sa.UUID(), nullable=False),
        sa.Column('tipo', tipo_pedido_t, nullable=False),
        sa.Column('diagnostico', sa.Text(), nullable=True),
        sa.Column('indicaciones', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['atencion_id'], ['atenciones.id']),
        sa.ForeignKeyConstraint(['medico_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # --- items_pedido ---
    op.create_table('items_pedido',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('pedido_id', sa.UUID(), nullable=False),
        sa.Column('descripcion', sa.String(length=255), nullable=False),
        sa.Column('codigo', sa.String(length=50), nullable=True),
        sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('items_pedido')
    op.drop_table('pedidos')
    op.drop_index('ix_estudios_catalogo_codigo', table_name='estudios_catalogo')
    op.drop_table('estudios_catalogo')
    op.drop_table('items_receta')
    op.drop_table('recetas')
    op.drop_table('evoluciones')
    op.drop_table('signos_vitales')
    op.drop_constraint('ck_adjunto_owner', 'adjuntos', type_='check')
    op.drop_constraint('fk_adjuntos_atencion_id', 'adjuntos', type_='foreignkey')
    op.drop_column('adjuntos', 'atencion_id')
    op.alter_column('adjuntos', 'licencia_id', existing_type=sa.UUID(), nullable=False)
    op.drop_table('atenciones')
    conn = op.get_bind()
    conn.execute(sa.text("DROP TYPE IF EXISTS tipo_pedido"))
    conn.execute(sa.text("DROP TYPE IF EXISTS tipo_estudio"))
    conn.execute(sa.text("DROP TYPE IF EXISTS estado_atencion"))
