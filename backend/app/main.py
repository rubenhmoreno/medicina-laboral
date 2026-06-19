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

    from app.modules.usuarios.router import router as auth_router, users_router

    app.include_router(auth_router)
    app.include_router(users_router)

    from app.modules.areas.router import router as areas_router
    app.include_router(areas_router)

    from app.modules.categorias.router import router as categorias_router
    app.include_router(categorias_router)

    from app.modules.tipos_licencia.router import router as tipos_licencia_router
    app.include_router(tipos_licencia_router)

    from app.modules.diagnosticos.router import router as diagnosticos_router
    app.include_router(diagnosticos_router)

    from app.modules.topes.router import router as topes_router
    app.include_router(topes_router)

    from app.modules.empleados.router import router as empleados_router
    app.include_router(empleados_router)

    from app.modules.adjuntos.router import router as adjuntos_router
    app.include_router(adjuntos_router)

    from app.modules.licencias.router import router as licencias_router
    app.include_router(licencias_router)

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
