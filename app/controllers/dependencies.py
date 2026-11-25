from typing import Annotated
from fastapi import Query

from app.schemas.common import (DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, PaginationParams)

def get_pagination(
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
) -> PaginationParams:
    return PaginationParams(page=page, size=size)