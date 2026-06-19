"""Local conftest for adjuntos tests.

The Adjunto model references the licencias table which does not exist yet (Phase 6).
The db_session fixture is mocked here because validation tests never hit the DB.
"""
import pytest


@pytest.fixture
def db_session():
    """Stub session — validation tests never hit the DB."""
    from unittest.mock import AsyncMock
    return AsyncMock()
