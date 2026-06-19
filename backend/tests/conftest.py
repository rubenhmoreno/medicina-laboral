import asyncio
import os
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.core.db import sessionmaker_factory

_TEST_ENV = {
    "POSTGRES_USER": "u",
    "POSTGRES_PASSWORD": "p",
    "POSTGRES_DB": "db",
    "POSTGRES_HOST": "h",
    "POSTGRES_PORT": "5432",
    "MINIO_ROOT_USER": "mu",
    "MINIO_ROOT_PASSWORD": "mp",
    "MINIO_BUCKET": "b",
    "MINIO_ENDPOINT": "m:9000",
    "MINIO_USE_SSL": "false",
    "APP_ENV": "test",
    "APP_SECRET_KEY": "x" * 32,
    "JWT_ACCESS_TTL_MINUTES": "15",
    "JWT_REFRESH_TTL_DAYS": "7",
}


@pytest.fixture(scope="session", autouse=True)
def _settings_env():
    """Provide minimal env vars so get_settings() succeeds in tests."""
    from app.core.settings import get_settings

    get_settings.cache_clear()
    with patch.dict(os.environ, _TEST_ENV, clear=False):
        yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16-alpine", driver="asyncpg") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_dsn(pg_container) -> str:
    return pg_container.get_connection_url()


@pytest_asyncio.fixture(scope="session")
async def _create_tables(db_dsn):
    """Create all tables in testcontainers DB once per session."""
    from app.core.db_base import Base
    engine = create_async_engine(db_dsn)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_dsn, _create_tables) -> AsyncGenerator[AsyncSession, None]:
    factory = sessionmaker_factory(db_dsn)
    async with factory() as session:
        yield session
        await session.rollback()
