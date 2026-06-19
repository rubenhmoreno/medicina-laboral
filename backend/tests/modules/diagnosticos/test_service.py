import pytest
from app.modules.diagnosticos.schemas import DiagnosticoCreate
from app.modules.diagnosticos.service import create_diagnostico


@pytest.mark.asyncio
async def test_create_diagnostico_basic(db_session):
    d = await create_diagnostico(db_session, DiagnosticoCreate(
        codigo_cie10="J06.9", descripcion="Infección respiratoria aguda",
        categoria="infeccioso", requiere_junta=False,
    ))
    assert d.id is not None
    assert d.categoria == "infeccioso"
