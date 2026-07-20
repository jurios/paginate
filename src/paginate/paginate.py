from __future__ import annotations

import math
from typing import TYPE_CHECKING

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from paginate.page_params import PageParams
from paginate.paginated_response import PaginatedResponse

if TYPE_CHECKING:
    from sqlmodel.sql.expression import SelectOfScalar


def paginate[T](
    session: Session,
    statement: Select[tuple[T]] | SelectOfScalar[T],
    params: PageParams,
) -> PaginatedResponse[T]:
    count_stmt = select(func.count()).select_from(statement.subquery())
    total = session.execute(count_stmt).scalar_one()

    paginated_stmt = statement.offset(params.offset).limit(params.per_page)
    items = session.execute(paginated_stmt).scalars().all()

    total_pages = math.ceil(total / params.per_page) if total > 0 else 1

    return PaginatedResponse(
        data=list(items),
        total=total,
        page=params.page,
        per_page=params.per_page,
        total_pages=total_pages,
        has_next=params.page < total_pages,
        has_prev=params.page > 1,
    )
