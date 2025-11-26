"""
Pagination utilities for API endpoints
"""
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from fastapi import Query
from math import ceil


T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Query(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Query(50, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database query."""
        return self.page_size


class Page(BaseModel, Generic[T]):
    """
    Paginated response wrapper.

    Generic pagination container that wraps any list of items.
    """
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        params: PaginationParams
    ) -> "Page[T]":
        """
        Create paginated response.

        Args:
            items: List of items for current page
            total: Total number of items
            params: Pagination parameters

        Returns:
            Page object with metadata
        """
        total_pages = ceil(total / params.page_size) if total > 0 else 1

        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1
        )


class CursorPaginationParams(BaseModel):
    """Cursor-based pagination for efficient large dataset queries."""
    cursor: Optional[str] = Query(None, description="Cursor for next page")
    limit: int = Query(50, ge=1, le=100, description="Items per page")


class CursorPage(BaseModel, Generic[T]):
    """Cursor-based paginated response."""
    items: List[T]
    next_cursor: Optional[str]
    has_next: bool

    @classmethod
    def create(
        cls,
        items: List[T],
        next_cursor: Optional[str] = None
    ) -> "CursorPage[T]":
        """Create cursor-based page."""
        return cls(
            items=items,
            next_cursor=next_cursor,
            has_next=next_cursor is not None
        )
