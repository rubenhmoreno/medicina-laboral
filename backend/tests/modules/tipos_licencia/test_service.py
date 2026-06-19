import pytest
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.shared.exceptions import ConflictError


@pytest.mark.asyncio
async def test_unique_codigo(db_session):
    await create_tipo(db_session, TipoLicenciaCreate(codigo="enfermedad-comun", nombre="Enfermedad común"))
    with pytest.raises(ConflictError):
        await create_tipo(db_session, TipoLicenciaCreate(codigo="enfermedad-comun", nombre="x"))
