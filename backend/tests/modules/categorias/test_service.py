import pytest
from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.shared.exceptions import ConflictError


@pytest.mark.asyncio
async def test_unique_codigo(db_session):
    await create_categoria(db_session, CategoriaCreate(codigo="planta-permanente", nombre="Planta"))
    with pytest.raises(ConflictError):
        await create_categoria(db_session, CategoriaCreate(codigo="planta-permanente", nombre="x"))
