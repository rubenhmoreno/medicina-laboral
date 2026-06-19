from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()

# Conservative local blocklist; can be swapped for zxcvbn if desired.
_COMMON = {
    "password",
    "password123",
    "qwerty",
    "letmein",
    "admin",
    "welcome",
    "iloveyou",
    "1234567890",
    "password1!",
    "password123!",
}


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, stored: str) -> bool:
    try:
        return _ph.verify(stored, plain)
    except VerifyMismatchError:
        return False


def validate_password_strength(plain: str) -> None:
    if len(plain) < 1:
        raise ValueError("password must not be empty")
