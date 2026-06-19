import pytest

from app.core.security import hash_password, validate_password_strength, verify_password


def test_hash_and_verify_round_trip():
    h = hash_password("CorrectHorseBatteryStaple9!")
    assert verify_password("CorrectHorseBatteryStaple9!", h) is True
    assert verify_password("wrong", h) is False


@pytest.mark.parametrize("bad", ["short", "alllowercase123456", "password123!"])
def test_weak_password_rejected(bad):
    with pytest.raises(ValueError):
        validate_password_strength(bad)


def test_strong_password_accepted():
    validate_password_strength("Tr0ub4dor&3Horse!Battery")
