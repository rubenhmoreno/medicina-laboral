import os
from unittest.mock import patch

from app.core.settings import Settings


def test_settings_reads_env_vars():
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
        "APP_ENV": "dev",
        "APP_SECRET_KEY": "x" * 32,
        "JWT_ACCESS_TTL_MINUTES": "15",
        "JWT_REFRESH_TTL_DAYS": "7",
        "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173",
    }
    with patch.dict(os.environ, env, clear=True):
        s = Settings()
    assert s.db_dsn == "postgresql+asyncpg://u:p@h:5432/db"
    assert s.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert s.app_secret_key.get_secret_value() == "x" * 32


def test_settings_rejects_short_secret():
    env = {"APP_SECRET_KEY": "short"}
    with patch.dict(os.environ, env, clear=False):
        try:
            Settings()
        except ValueError as e:
            assert "secret" in str(e).lower()
            return
        raise AssertionError("Expected ValueError")
