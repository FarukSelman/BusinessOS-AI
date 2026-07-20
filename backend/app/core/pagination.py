from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    items: list[T]

    page: int

    size: int

    total: int

    pages: int

    @classmethod
    def create(
        cls,
        *,
        items: list[T],
        total: int,
        page: int,
        size: int,
    ):

        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=ceil(total / size) if total else 0,
        )