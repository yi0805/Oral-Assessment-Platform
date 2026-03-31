"""Shared pagination schema used by all list endpoints."""
from __future__ import annotations

import math
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """
    Paginated list response envelope.

    All list endpoints accept `page` (1-based) and `page_size` query parameters
    and return this wrapper instead of a bare list.

    Example response:
        {
          "items": [...],
          "total": 42,
          "page": 2,
          "page_size": 20,
          "total_pages": 3
        }
    """

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, page_size: int) -> "Page[T]":
        total_pages = max(1, math.ceil(total / page_size)) if total else 1
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
