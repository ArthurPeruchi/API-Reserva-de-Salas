from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.controllers import room_controller
from app.core.exceptions import ConflictError, NotFoundError


def create_app() -> FastAPI:
    app = FastAPI(title="API de Reserva de Salas", version="1.0.0", description="API para gerenciar reservas de salas")

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/api/health", tags=["Health"])
    def health_check():
        return {"status": "ok"}

    app.include_router(room_controller.router)

    @app.exception_handler(NotFoundError)
    def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    return app

app = create_app()
