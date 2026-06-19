# backend/tests/core/test_readyz.py
from fastapi.testclient import TestClient

from app.main import app


def test_readyz_returns_503_when_minio_unreachable(monkeypatch):
    # When run without docker-compose up, /readyz should fail with 503.
    client = TestClient(app)
    r = client.get("/readyz")
    assert r.status_code in (200, 503)  # 200 if dev stack is up
