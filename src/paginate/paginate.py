import math

from sqlalchemy import func
from sqlmodel import Session, SQLModel, select
from sqlmodel.sql.expression import SelectOfScalar

from paginate.page_params import PageParams
from paginate.paginated_response import PaginatedResponse


def paginate[T: SQLModel](
    session: Session,
    statement: SelectOfScalar[T],
    params: PageParams,
) -> PaginatedResponse[T]:
    """
    Paginates any SQLModel select() statement.

    Applies the correct OFFSET/LIMIT and runs a count query that
    respects all filters already chained onto the statement.

    Args:
        session:    Active SQLModel/SQLAlchemy session.
        statement:  A select() statement, optionally with .where() filters applied.
        params:     PageParams instance injected by FastAPI.

    Returns:
        PagedResponse with the current page's items and pagination metadata.

    Example:
        stmt = select(Hero).where(Hero.age > 18).order_by(Hero.id)
        return paginate(session, stmt, params)
    """
    # Count total matching rows using the filtered statement as a subquery,
    # so filters are respected and we don't count the entire table
    count_stmt = select(func.count()).select_from(statement.subquery())
    total = session.exec(count_stmt).one()

    # Fetch only the items for the requested page
    paginated_stmt = statement.offset(params.offset).limit(params.per_page)
    items = session.exec(paginated_stmt).all()

    # Avoid division by zero when the result set is empty
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
