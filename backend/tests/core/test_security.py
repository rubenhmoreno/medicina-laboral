import pytest

from app.core.security import hash_password, validate_password_strength, verify_password


def test_hash_and_verify_round_trip():
    h = hash_password("CorrectHorseBatteryStaple9!")
    assert verify_password("CorrectHorseBatteryStaple9!", h) is True
    assert verify_password("wrong", h) is False


def test_empty_password_rejected():
    with pytest.raises(ValueError):
        validate_password_strength("")


def test_any_password_accepted():
    validate_password_strength("123")
    validate_password_strength("a")
    validate_password_strength("Tr0ub4dor&3Horse!Battery")
