from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, cast, overload

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from paginate.page_params import PageParams
from paginate.paginated_response import PaginatedResponse

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlmodel.sql.expression import SelectOfScalar


@overload
def paginate[T](
    session: Session,
    statement: Select[tuple[T]] | SelectOfScalar[T],
    params: PageParams,
    *,
    mapper: None = None,
) -> PaginatedResponse[T]: ...


@overload
def paginate[T, R](
    session: Session,
    statement: Select[tuple[T]] | SelectOfScalar[T],
    params: PageParams,
    *,
    mapper: Callable[[T], R],
) -> PaginatedResponse[R]: ...


def paginate[T, R](
    session: Session,
    statement: Select[tuple[T]] | SelectOfScalar[T],
    params: PageParams,
    *,
    mapper: Callable[[T], R] | None = None,
) -> PaginatedResponse[T] | PaginatedResponse[R]:
    count_stmt = select(func.count()).select_from(statement.subquery())
    total = session.execute(count_stmt).scalar_one()

    paginated_stmt = statement.offset(params.offset).limit(params.per_page)
    items = session.execute(paginated_stmt).scalars().all()

    data: list[T] | list[R] = (
        list(items) if mapper is None else [mapper(item) for item in items]
    )

    total_pages = math.ceil(total / params.per_page) if total > 0 else 1

    return cast(
        "PaginatedResponse[T] | PaginatedResponse[R]",
        PaginatedResponse[Any](
            data=data,
            total=total,
            page=params.page,
            per_page=params.per_page,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_prev=params.page > 1,
        ),
    )
