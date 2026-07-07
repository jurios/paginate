from fastapi import Query


class PageParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number"),
        per_page: int = Query(
            default=20, ge=1, le=100, description="Number of items per page"
        ),
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page
