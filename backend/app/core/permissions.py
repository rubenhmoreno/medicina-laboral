# backend/app/core/permissions.py
from collections.abc import Callable

from fastapi import Depends

from app.core.deps import current_user
from app.modules.usuarios.models import Rol, Usuario
from app.shared.exceptions import ForbiddenError


def require_role(*roles: Rol) -> Callable[..., object]:
    async def dep(user: Usuario = Depends(current_user)) -> Usuario:
        if user.rol not in roles:
            raise ForbiddenError("insufficient permissions", detail={"required": [r.value for r in roles]})
        return user

    return dep
