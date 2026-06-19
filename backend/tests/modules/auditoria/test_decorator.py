from typing import ClassVar

import pytest
from sqlalchemy import select

from app.modules.auditoria.decorator import audited
from app.modules.auditoria.models import Auditoria


class FakeUser:
    id = None


class FakeRequest:
    headers: ClassVar = {"user-agent": "ua"}
    class _C:
        host = "1.2.3.4"
    client = _C()


@pytest.mark.asyncio
async def test_audited_writes_entry(db_session):
    @audited("create", "ficticio")
    async def service(*, session, request, current_user, value):
        return type("R", (), {"id": None, "value": value})()

    await service(session=db_session, request=FakeRequest(), current_user=FakeUser(), value="x")
    await db_session.flush()
    rows = (await db_session.execute(select(Auditoria))).scalars().all()
    assert any(r.accion == "create" and r.entidad == "ficticio" for r in rows)
