from fastapi import FastAPI
from fastapi.responses import RedirectResponse

def create_app() -> FastAPI:
    app = FastAPI(title="API de Reserva de Salas", version="1.0.0", description="API para gerenciar reservas de salas")

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/api/health", tags=["Health"])
    def health_check():
        return {"status": "ok"}

    return app

app = create_app()