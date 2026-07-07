from unittest.mock import MagicMock

import pytest
from sqlalchemy import literal
from sqlalchemy import select as sa_select


@pytest.fixture
def statement():
    stmt = MagicMock(name="statement")
    stmt.subquery.return_value = sa_select(literal(1)).subquery()
    return stmt


@pytest.fixture
def session():
    s = MagicMock(name="session")
    s.exec.return_value.one.return_value = 0
    s.exec.return_value.all.return_value = []
    return s
