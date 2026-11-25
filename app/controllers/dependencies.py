from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.models import User

DbSession = Annotated[Session, Depends(get_db)]


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
