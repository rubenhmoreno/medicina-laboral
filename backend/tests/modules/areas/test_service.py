import pytest

from app.modules.areas.schemas import AreaCreate
from app.modules.areas.service import create_area
from app.shared.exceptions import ConflictError


@pytest.mark.asyncio
async def test_duplicate_name_rejected(db_session):
    await create_area(db_session, AreaCreate(nombre="RRHH"))
    with pytest.raises(ConflictError):
        await create_area(db_session, AreaCreate(nombre="RRHH"))
