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

CUSTOM_VALUE_ERROR_PREFIX = "Value error, "

VALIDATION_MESSAGES = {
    "missing": "Campo obrigatório.",
    "string_type": "Deve ser um texto.",
    "int_type": "Deve ser um número inteiro.",
    "int_parsing": "Deve ser um número inteiro.",
    "int_from_float": "Deve ser um número inteiro.",
    "float_type": "Deve ser um número.",
    "float_parsing": "Deve ser um número.",
    "bool_type": "Deve ser verdadeiro ou falso.",
    "bool_parsing": "Deve ser verdadeiro ou falso.",
    "greater_than": "Deve ser maior que {gt}.",
    "greater_than_equal": "Deve ser maior ou igual a {ge}.",
    "less_than": "Deve ser menor que {lt}.",
    "less_than_equal": "Deve ser menor ou igual a {le}.",
    "string_too_short": "Deve ter no mínimo {min_length} caractere(s).",
    "string_too_long": "Deve ter no máximo {max_length} caractere(s).",
    "string_pattern_mismatch": "Formato inválido.",
    "literal_error": "Valor não permitido.",
    "extra_forbidden": "Campo não permitido.",
    "datetime_type": "Data e hora inválidas. Use o formato ISO 8601.",
    "datetime_parsing": "Data e hora inválidas. Use o formato ISO 8601.",
    "datetime_from_date_parsing": "Data e hora inválidas. Use o formato ISO 8601.",
}

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
def format_field(location: tuple[str | int, ...]) -> str:
    parts = list(location)
    if parts and parts[0] in LOCATION_PREFIXES:
        parts = parts[1:]
    return ".".join(str(part) for part in parts)

def translate_validation_message(detail: dict) -> str:
    error_type = detail["type"]
    original_message = detail["msg"]

    if original_message.startswith(CUSTOM_VALUE_ERROR_PREFIX):
        return original_message[len(CUSTOM_VALUE_ERROR_PREFIX):]

    if error_type == "value_error":
        if "email" in original_message.lower():
            return "E-mail inválido."
        return "Valor inválido."

    template = VALIDATION_MESSAGES.get(error_type)
    if template is None:
        return original_message

    try:
        return template.format(**detail.get("ctx", {}))
    except (KeyError, IndexError, ValueError):
        return original_message

async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return build_error_response(exc.status_code, exc.message)

async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = exc.errors()

    if any(detail["type"] == "json_invalid" for detail in details):
        return build_error_response(400, "JSON malformado.")

    errors = [
        {
            "field": format_field(detail["loc"]), 
            "message": translate_validation_message(detail)
        }
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