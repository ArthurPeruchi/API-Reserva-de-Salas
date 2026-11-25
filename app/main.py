from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.controllers.error_handlers import register_error_handlers

from app.controllers import room_controller
from app.controllers.error_handlers import register_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="API de Reserva de Salas", version="1.0.0", description="API para gerenciar reservas de salas")

    register_error_handlers(app)
    
    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/api/health", tags=["Health"])
    def health_check():
        return {"status": "ok"}

    app.include_router(room_controller.router)

    return app

app = create_app()
