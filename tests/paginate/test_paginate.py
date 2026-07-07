import pytest
from sqlmodel import SQLModel

from paginate.page_params import PageParams
from paginate.paginate import paginate


class TestPaginate:
    CASES = [
        pytest.param(0, 1, 10, 1, False, False, id="empty-result-set"),
        pytest.param(5, 1, 10, 1, False, False, id="single-partial-page"),
        pytest.param(10, 1, 10, 1, False, False, id="single-exact-page"),
        pytest.param(11, 1, 10, 2, True, False, id="first-of-two"),
        pytest.param(11, 2, 10, 2, False, True, id="last-of-two"),
        pytest.param(25, 1, 10, 3, True, False, id="first-of-three"),
        pytest.param(25, 2, 10, 3, True, True, id="middle-of-three"),
        pytest.param(25, 3, 10, 3, False, True, id="last-of-three"),
        pytest.param(20, 2, 10, 2, False, True, id="exact-division-last-page"),
        pytest.param(100, 5, 20, 5, False, True, id="larger-page-size"),
        pytest.param(1, 1, 1, 1, False, False, id="one-per-page-single"),
        pytest.param(3, 2, 1, 3, True, True, id="one-per-page-middle"),
    ]

    @pytest.mark.parametrize(
        "total, page, per_page, exp_pages, exp_next, exp_prev", CASES
    )
    def test_metadata(
        self, session, statement, total, page, per_page, exp_pages, exp_next, exp_prev
    ):
        session.exec.return_value.one.return_value = total
        session.exec.return_value.all.return_value = []

        params = PageParams(page=page, per_page=per_page)

        response = paginate(session, statement, params)

        assert response.total == total
        assert response.total_pages == exp_pages
        assert response.has_next is exp_next
        assert response.has_prev is exp_prev
        assert response.page is page
        assert response.per_page is per_page

    def test_applies_offset_then_limit_from_params(self, session, statement):
        paginate(session, statement, PageParams(page=3, per_page=15))

        statement.offset.assert_called_once_with(30)
        statement.offset.return_value.limit.assert_called_once_with(15)

    def test_data_holds_the_items_from_the_page_query(self, session, statement):
        items = [SQLModel(id=1), SQLModel(id=2)]
        session.exec.return_value.one.return_value = len(items)
        session.exec.return_value.all.return_value = items

        response = paginate(session, statement, PageParams(page=1, per_page=10))

        assert response.data == items
        assert isinstance(response.data, list)
