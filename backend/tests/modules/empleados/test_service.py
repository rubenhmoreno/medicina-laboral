from datetime import date

import pytest

from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.empleados.schemas import EmpleadoCreate
from app.modules.empleados.service import create_empleado
from app.shared.exceptions import ConflictError, NotFoundError


@pytest.mark.asyncio
async def test_create_requires_existing_categoria(db_session):
    import uuid
    with pytest.raises(NotFoundError):
        await create_empleado(db_session, EmpleadoCreate(
            legajo="L1", cuil="20111111119", nombre="A", apellido="B",
            fecha_ingreso=date(2020, 1, 1), categoria_id=uuid.uuid4(),
        ))


@pytest.mark.asyncio
async def test_duplicate_legajo(db_session):
    cat = await create_categoria(db_session, CategoriaCreate(codigo="planta", nombre="P"))
    await db_session.flush()
    base = EmpleadoCreate(legajo="L1", cuil="20111111119", nombre="A", apellido="B",
                          fecha_ingreso=date(2020, 1, 1), categoria_id=cat.id)
    await create_empleado(db_session, base)
    with pytest.raises(ConflictError):
        await create_empleado(db_session, base.model_copy(update={"cuil": "20222222222"}))
