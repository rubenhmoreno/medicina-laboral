import pytest

from app.core.db import execute_select_one, get_session, sessionmaker_factory
from app.core.settings import get_settings


@pytest.mark.asyncio
async def test_session_can_execute_select_one():
    factory = sessionmaker_factory(get_settings().db_dsn)
    async for session in get_session(factory):
        assert await execute_select_one(session) == 1
        break
