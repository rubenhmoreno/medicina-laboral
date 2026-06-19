from app.modules.licencias.models import EstadoLicencia as E
from app.modules.usuarios.models import Rol
from app.shared.exceptions import InvalidStateTransition

# (from, to) -> roles allowed
_RULES: dict[tuple[E, E], set[Rol]] = {
    (E.BORRADOR, E.ENVIADO):   {Rol.RRHH, Rol.MEDICO, Rol.ADMIN},
    (E.BORRADOR, E.ANULADO):   {Rol.RRHH, Rol.MEDICO, Rol.ADMIN},
    (E.ENVIADO,  E.VALIDADO):  {Rol.MEDICO, Rol.ADMIN},
    (E.ENVIADO,  E.RECHAZADO): {Rol.MEDICO, Rol.ADMIN},
    (E.VALIDADO, E.ANULADO):   {Rol.ADMIN},
    (E.RECHAZADO, E.BORRADOR): {Rol.ADMIN},
}

# Map action name -> target state.
_ACTIONS = {
    "enviar":   E.ENVIADO,
    "validar":  E.VALIDADO,
    "rechazar": E.RECHAZADO,
    "anular":   E.ANULADO,
    "reabrir":  E.BORRADOR,
}


def can_transition(from_state: E, to_state: E, role: Rol) -> bool:
    return role in _RULES.get((from_state, to_state), set())


def next_state(current: E, action: str, role: Rol) -> E:
    if action not in _ACTIONS:
        raise InvalidStateTransition(f"acción desconocida: {action}")
    target = _ACTIONS[action]
    if not can_transition(current, target, role):
        raise InvalidStateTransition(
            f"transición {current.value} → {target.value} no permitida para rol {role.value}",
            detail={"from": current.value, "to": target.value, "role": role.value},
        )
    return target
