# backend/tests/modules/auditoria/test_models.py
import pytest
from sqlalchemy import select

from app.modules.auditoria.models import Auditoria


@pytest.mark.asyncio
async def test_can_insert_audit_row(db_session):
    row = Auditoria(accion="login", entidad="usuario", payload={"ok": True})
    db_session.add(row)
    await db_session.flush()
    result = await db_session.execute(select(Auditoria))
    assert result.scalar_one().accion == "login"
