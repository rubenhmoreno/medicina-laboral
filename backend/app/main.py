from fastapi import FastAPI

from app.shared.error_handler import install_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="medicia-laboral", version="0.1.0")
    install_error_handlers(app)

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
