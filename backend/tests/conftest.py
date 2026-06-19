import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.core.db import sessionmaker_factory


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
