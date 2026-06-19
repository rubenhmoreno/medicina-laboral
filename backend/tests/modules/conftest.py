"""Module-level conftest.

Removes tables that depend on not-yet-existing tables (Phase 6+) from
Base.metadata so that the session-scoped create_all does not fail.
"""
import pytest

from app.core.db_base import Base


@pytest.fixture(scope="session", autouse=True)
def _exclude_future_tables():
    """Exclude tables whose FK targets do not exist yet from create_all."""
    for table_name in ("adjuntos",):
        table = Base.metadata.tables.get(table_name)
        if table is not None:
            Base.metadata.remove(table)
    yield
