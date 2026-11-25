from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.models import User
from app.schemas.common import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, PaginationParams

DbSession = Annotated[Session, Depends(get_db)]


def get_pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> PaginationParams:
    """Lê e valida page e size da query string."""
    return PaginationParams(page=page, size=size)


def require_admin(
    session: DbSession,
    x_user_id: Annotated[int | None, Header(description="ID do usuário (provisório até o JWT)")] = None,
) -> User:
    user = session.get(User, x_user_id) if x_user_id is not None else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não autenticado.")
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Acesso restrito a administradores.")
    return user
