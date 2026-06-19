from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt  # type: ignore[import-untyped]

from app.core.settings import Settings

_ALG = "HS256"


def _now() -> datetime:
    return datetime.now(timezone.utc)  # noqa: UP017


def issue_access(subject: str, settings: Settings) -> str:
    now = _now()
    payload = {
        "sub": subject,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_access_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.app_secret_key.get_secret_value(), algorithm=_ALG)  # type: ignore[no-any-return]


def issue_refresh(subject: str, settings: Settings) -> str:
    now = _now()
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.jwt_refresh_ttl_days)).timestamp()),
    }
    return jwt.encode(payload, settings.app_secret_key.get_secret_value(), algorithm=_ALG)  # type: ignore[no-any-return]


def decode_token(token: str, settings: Settings) -> dict[str, Any]:
    return jwt.decode(token, settings.app_secret_key.get_secret_value(), algorithms=[_ALG])  # type: ignore[no-any-return]
