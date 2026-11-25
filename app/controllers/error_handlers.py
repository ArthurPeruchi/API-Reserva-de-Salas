import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions import AppError

logger = logging.getLogger(__name__)

DEFAULT_HTTP_MESSAGES = {
    404: "Rota não encontrada.",
    405: "Método não permitido.",
}

LOCATION_PREFIXES = ("body", "query", "path")

def build_error_response(
    status_code: int,
    message: str,
    errors: list[dict] | None = None,
    headers: dict | None = None,
) -> JSONResponse:
    body: dict = {
        "status": status_code, 
        "message": message
    }
    if errors is not None:
        body["errors"] = errors

    return JSONResponse(status_code=status_code, content=body, headers=headers)

# Transforma ('body', 'capacity') em 'capacity'
def format_field(location: tuple) -> str:
    parts = list(location)
    if parts and parts[0] in LOCATION_PREFIXES:
        parts = parts[1:]
    return ".".join(str(part) for part in parts)

async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return build_error_response(exc.status_code, exc.message)

async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = exc.errors()

    if any(detail["type"] == "json_invalid" for detail in details):
        return build_error_response(400, "JSON malformado.")

    errors = [
        {"field": format_field(detail["loc"]), "message": detail["msg"]}
        for detail in details
    ]
    return build_error_response(422, "Dados inválidos.", errors)

async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = DEFAULT_HTTP_MESSAGES.get(exc.status_code, str(exc.detail))
    return build_error_response(exc.status_code, message, headers=exc.headers)

async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro inesperado em %s %s", request.method, request.url.path)
    return build_error_response(500, "Erro interno do servidor.")

def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_error)
    app.add_exception_handler(Exception, handle_unexpected_error)