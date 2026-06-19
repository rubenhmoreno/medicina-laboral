import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from app.core.settings import get_settings

# Imports below register tables; populated in later tasks.
from app.modules.usuarios import models as _usuarios_models  # noqa: F401
from app.modules.empleados import models as _empleados_models  # noqa: F401

from app.core.db_base import Base  # see Task 1.7
from app.modules.auditoria.models import Auditoria  # noqa: F401
from app.modules.areas import models as _areas_models  # noqa: F401
from app.modules.categorias import models as _categorias_models  # noqa: F401
from app.modules.tipos_licencia import models as _tipos_licencia_models  # noqa: F401
from app.modules.diagnosticos import models as _diagnosticos_models  # noqa: F401
from app.modules.topes import models as _topes_models  # noqa: F401
from app.modules.licencias import models as _lic_models  # noqa: F401
from app.modules.adjuntos import models as _adj_models   # noqa: F401

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
config.set_main_option("sqlalchemy.url", get_settings().db_dsn)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
