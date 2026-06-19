"""Idempotent seed for dev/CI. Creates 1 admin + 1 médico + 1 rrhh + base catálogos."""
import asyncio

from app.core.db import sessionmaker_factory
from app.core.settings import get_settings
from app.modules.categorias.schemas import CategoriaCreate
from app.modules.categorias.service import create_categoria
from app.modules.tipos_licencia.schemas import TipoLicenciaCreate
from app.modules.tipos_licencia.service import create_tipo
from app.modules.usuarios.models import Rol
from app.modules.usuarios.repository import get_by_email
from app.modules.usuarios.schemas import UsuarioCreate
from app.modules.usuarios.service import create_user

SETTINGS = get_settings()


async def main():
    factory = sessionmaker_factory(SETTINGS.db_dsn)
    async with factory() as s:
        # Users
        if not await get_by_email(s, "admin"):
            await create_user(s, UsuarioCreate(
                email="admin",
                password="123",
                nombre="Administrador", rol=Rol.ADMIN,
            ))
        if not await get_by_email(s, "medico"):
            await create_user(s, UsuarioCreate(
                email="medico",
                password="123",
                nombre="Medico", rol=Rol.MEDICO, matricula="MN12345",
            ))
        if not await get_by_email(s, "secretaria"):
            await create_user(s, UsuarioCreate(
                email="secretaria",
                password="123",
                nombre="Secretaria", rol=Rol.RRHH,
            ))

        # Categorías base
        for codigo, nombre in [
            ("planta-permanente", "Planta permanente"),
            ("contratado", "Contratado"),
            ("monotributista", "Monotributista"),
        ]:
            try:
                await create_categoria(s, CategoriaCreate(codigo=codigo, nombre=nombre))
            except Exception:
                pass

        # Tipos de licencia base
        for codigo, nombre in [
            ("enfermedad-comun", "Enfermedad común"),
            ("accidente-trabajo", "Accidente de trabajo"),
            ("examen-medico", "Examen médico"),
            ("maternidad", "Maternidad"),
            ("larga-enfermedad", "Larga enfermedad"),
        ]:
            try:
                await create_tipo(s, TipoLicenciaCreate(codigo=codigo, nombre=nombre))
            except Exception:
                pass

        await s.commit()
        print("Seed OK")


if __name__ == "__main__":
    asyncio.run(main())
