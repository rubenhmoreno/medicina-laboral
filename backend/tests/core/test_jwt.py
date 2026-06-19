import os
from unittest.mock import patch

import pytest
from freezegun import freeze_time
from jose.exceptions import ExpiredSignatureError

from app.core.jwt import decode_token, issue_access, issue_refresh
from app.core.settings import Settings


@pytest.fixture
def settings():
    env = {
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "db",
        "POSTGRES_HOST": "h",
        "POSTGRES_PORT": "5432",
        "MINIO_ROOT_USER": "mu",
        "MINIO_ROOT_PASSWORD": "mp",
        "MINIO_BUCKET": "b",
        "MINIO_ENDPOINT": "m:9000",
        "MINIO_USE_SSL": "false",
        "APP_ENV": "test",
        "APP_SECRET_KEY": "x" * 32,
        "JWT_ACCESS_TTL_MINUTES": "15",
        "JWT_REFRESH_TTL_DAYS": "7",
    }
    with patch.dict(os.environ, env, clear=True):
        yield Settings()


def test_access_and_refresh_round_trip(settings):
    sub = "user-123"
    access = issue_access(sub, settings)
    refresh = issue_refresh(sub, settings)
    a = decode_token(access, settings)
    r = decode_token(refresh, settings)
    assert a["sub"] == sub and a["type"] == "access"
    assert r["sub"] == sub and r["type"] == "refresh"


def test_expired_access_raises(settings):
    with freeze_time("2026-01-01"):
        t = issue_access("u", settings)
    with freeze_time("2026-01-02"), pytest.raises(ExpiredSignatureError):
        decode_token(t, settings)
