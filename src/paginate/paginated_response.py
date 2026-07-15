from pydantic import BaseModel


class PaginatedResponse[T](BaseModel):
    """Generic paginated response wrapper. Works with any SQLModel schema."""

    data: list[T]  # Items for the current page
    total: int  # Total number of matching records
    page: int  # Current page number
    per_page: int  # Page size used for this request
    total_pages: int  # Total number of available pages
    has_next: bool  # Whether a next page exists
    has_prev: bool  # Whether a previous page exists
