from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.error_handler import install_error_handlers
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError


def make_app():
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/notfound")
    def nf():
        raise NotFoundError("missing", detail={"id": 1})

    @app.get("/conflict")
    def cf():
        raise ConflictError("dup", detail={"field": "email"})

    @app.get("/validation")
    def vd():
        raise ValidationError("bad")

    @app.get("/boom")
    def boom():
        raise RuntimeError("kaboom")

    return TestClient(app, raise_server_exceptions=False)


def test_not_found_returns_404_with_envelope():
    r = make_app().get("/notfound")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["message"] == "missing"
    assert body["error"]["detail"] == {"id": 1}
    assert "request_id" in body


def test_conflict_returns_409():
    r = make_app().get("/conflict")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


def test_validation_returns_422():
    r = make_app().get("/validation")
    assert r.status_code == 422


def test_unexpected_returns_500_without_stacktrace():
    r = make_app().get("/boom")
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "internal_error"
    assert "kaboom" not in body["error"]["message"]
    assert "request_id" in body
