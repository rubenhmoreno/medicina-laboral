from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="medicia-laboral", version="0.1.0")

    @app.get("/healthz", tags=["ops"])
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
