# backend/app/main.py
from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.core.db import sessionmaker_factory
from app.core.logging import configure_logging
from app.core.middleware import install_request_id_middleware
from app.core.settings import get_settings
from app.core.storage import minio_client
from app.shared.error_handler import install_error_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(title="medicia-laboral", version="0.1.0")
    install_error_handlers(app)
    install_request_id_middleware(app)

    factory = sessionmaker_factory(settings.db_dsn)
    mc = minio_client(settings)

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["ops"])
    async def readyz() -> dict[str, str]:
        try:
            async with factory() as s:
                await s.execute(text("select 1"))
        except Exception as e:
            raise HTTPException(503, f"db: {e!s}") from e
        try:
            mc.bucket_exists(settings.minio_bucket)
        except Exception as e:
            raise HTTPException(503, f"minio: {e!s}") from e
        return {"status": "ready"}

    return app


app = create_app()
