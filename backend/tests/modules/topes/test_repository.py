from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.topes import repository as repo


@pytest.mark.asyncio
async def test_set_tope_closes_previous_version(db_session):
    cat = await create_categoria(db_session, CategoriaCreate(codigo="planta", nombre="P"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="ec", nombre="Enfermedad común"))
    await db_session.flush()

    t1 = await repo.set_tope(
        db_session, categoria_id=cat.id, tipo_licencia_id=tipo.id,
        dias_maximos=90, ventana="anio-aniversario",
        desde=date(2026, 1, 1), observacion="v1",
    )
    t2 = await repo.set_tope(
        db_session, categoria_id=cat.id, tipo_licencia_id=tipo.id,
        dias_maximos=120, ventana="anio-aniversario",
        desde=date(2026, 6, 1), observacion="v2",
    )
    # Re-read t1 to see its `vigente_hasta` was set.
    await db_session.refresh(t1)
    assert t1.vigente_hasta == date(2026, 6, 1)
    assert t2.vigente_hasta is None


@pytest.mark.asyncio
async def test_tope_vigente_picks_latest_active(db_session):
    cat = await create_categoria(db_session, CategoriaCreate(codigo="c", nombre="c"))
    tipo = await create_tipo(db_session, TipoLicenciaCreate(codigo="t", nombre="t"))
    await db_session.flush()
    await repo.set_tope(db_session, categoria_id=cat.id, tipo_licencia_id=tipo.id,
                       dias_maximos=30, ventana="anio-calendario",
                       desde=date(2025, 1, 1), observacion=None)
    await repo.set_tope(db_session, categoria_id=cat.id, tipo_licencia_id=tipo.id,
                       dias_maximos=60, ventana="anio-calendario",
                       desde=date(2026, 1, 1), observacion=None)
    found = await repo.tope_vigente(db_session, cat.id, tipo.id, en_fecha=date(2026, 6, 15))
    assert found is not None and found.dias_maximos == 60
