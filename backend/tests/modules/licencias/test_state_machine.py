import pytest

from app.modules.licencias.models import EstadoLicencia
from app.modules.licencias.state_machine import (
    can_transition,
    next_state,
)
from app.modules.usuarios.models import Rol
from app.shared.exceptions import InvalidStateTransition

E = EstadoLicencia

ALLOWED = [
    # (from, to, role, ok?)
    (E.BORRADOR, E.ENVIADO, Rol.RRHH, True),
    (E.BORRADOR, E.ENVIADO, Rol.MEDICO, True),
    (E.BORRADOR, E.ANULADO, Rol.RRHH, True),
    (E.BORRADOR, E.ANULADO, Rol.ADMIN, True),
    (E.ENVIADO, E.VALIDADO, Rol.MEDICO, True),
    (E.ENVIADO, E.VALIDADO, Rol.RRHH, False),
    (E.ENVIADO, E.RECHAZADO, Rol.MEDICO, True),
    (E.VALIDADO, E.ANULADO, Rol.ADMIN, True),
    (E.VALIDADO, E.ANULADO, Rol.MEDICO, False),
    (E.RECHAZADO, E.BORRADOR, Rol.ADMIN, True),
    (E.RECHAZADO, E.VALIDADO, Rol.ADMIN, False),  # bypass not allowed
    (E.ANULADO, E.BORRADOR, Rol.ADMIN, False),
]


@pytest.mark.parametrize("frm,to,role,ok", ALLOWED)
def test_matrix(frm, to, role, ok):
    if ok:
        assert can_transition(frm, to, role) is True
    else:
        assert can_transition(frm, to, role) is False


def test_next_state_raises_on_illegal():
    with pytest.raises(InvalidStateTransition):
        next_state(E.VALIDADO, "enviar", Rol.MEDICO)


def test_next_state_handles_enviar():
    assert next_state(E.BORRADOR, "enviar", Rol.RRHH) is E.ENVIADO
    assert next_state(E.ENVIADO, "validar", Rol.MEDICO) is E.VALIDADO
    assert next_state(E.ENVIADO, "rechazar", Rol.MEDICO) is E.RECHAZADO
    assert next_state(E.VALIDADO, "anular", Rol.ADMIN) is E.ANULADO
    assert next_state(E.RECHAZADO, "reabrir", Rol.ADMIN) is E.BORRADOR
