from fastapi import FastAPI

from app.core.logging import configure_logging
from app.core.middleware import install_request_id_middleware
from app.core.settings import get_settings
from app.shared.error_handler import install_error_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="medicia-laboral", version="0.1.0")
    install_error_handlers(app)
    install_request_id_middleware(app)

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
