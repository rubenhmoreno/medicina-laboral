import pytest

from app.core.db import execute_select_one


@pytest.mark.asyncio
async def test_session_can_execute_select_one(db_session):
    assert await execute_select_one(db_session) == 1
