from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import install_request_id_middleware


def test_response_carries_request_id_header():
    app = FastAPI()
    install_request_id_middleware(app)

    @app.get("/")
    def index():
        return {}

    r = TestClient(app).get("/")
    assert "x-request-id" in r.headers
    assert len(r.headers["x-request-id"]) >= 16


def test_request_id_is_echoed_when_provided():
    app = FastAPI()
    install_request_id_middleware(app)

    @app.get("/")
    def index():
        return {}

    r = TestClient(app).get("/", headers={"x-request-id": "abc-123"})
    assert r.headers["x-request-id"] == "abc-123"
