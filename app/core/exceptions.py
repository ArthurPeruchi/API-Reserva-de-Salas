class NotFoundError(Exception):
    """O recurso pedido não existe (vira HTTP 404)."""


class ConflictError(Exception):
    """A ação conflita com o estado atual do banco (vira HTTP 409)."""
