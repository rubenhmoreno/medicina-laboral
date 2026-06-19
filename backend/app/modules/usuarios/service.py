# backend/app/modules/usuarios/service.py
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, validate_password_strength, verify_password
from app.modules.usuarios import repository as repo
from app.modules.usuarios.models import Usuario
from app.modules.usuarios.schemas import UsuarioCreate
from app.shared.exceptions import ConflictError, UnauthorizedError


async def create_user(session: AsyncSession, payload: UsuarioCreate) -> Usuario:
    if await repo.get_by_email(session, payload.email):
        raise ConflictError("email already registered", detail={"field": "email"})
    validate_password_strength(payload.password)
    u = Usuario(
        email=payload.email,
        password_hash=hash_password(payload.password),
        nombre=payload.nombre,
        rol=payload.rol,
        matricula=payload.matricula,
    )
    return await repo.insert(session, u)


async def authenticate(session: AsyncSession, email: str, password: str) -> Usuario:
    u = await repo.get_by_email(session, email)
    if not u or not u.activo or not verify_password(password, u.password_hash):
        raise UnauthorizedError("invalid credentials")
    u.ultimo_login = datetime.now(UTC)
    await repo.update(session, u)
    return u
