from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel

ItemT = TypeVar("ItemT")

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

@dataclass(frozen=True)
class PaginationParams:
    page: int
    size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class Page(BaseModel, Generic[ItemT]):
    data: list[ItemT]
    page: int
    size: int
    total: int