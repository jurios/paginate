from __future__ import annotations

import dataclasses

from pydantic import BaseModel

from paginate.page_params import PageParams
from paginate.paginate import paginate
from tests.factories import Backend


@dataclasses.dataclass
class HeroDTO:
    label: str
    age: int


class HeroSchema(BaseModel):
    label: str
    age: int


def test_first_page(backend: Backend) -> None:
    resp = paginate(
        backend.session, backend.select_all(), PageParams(page=1, per_page=10)
    )

    assert resp.total == 25
    assert resp.total_pages == 3
    assert resp.page == 1
    assert resp.per_page == 10
    assert len(resp.data) == 10
    assert [h.age for h in resp.data] == list(range(0, 10))
    assert resp.has_prev is False
    assert resp.has_next is True


def test_middle_page(backend: Backend) -> None:
    resp = paginate(
        backend.session, backend.select_all(), PageParams(page=2, per_page=10)
    )

    assert len(resp.data) == 10
    assert [h.age for h in resp.data] == list(range(10, 20))
    assert resp.has_prev is True
    assert resp.has_next is True


def test_last_page_is_partial(backend: Backend) -> None:
    resp = paginate(
        backend.session, backend.select_all(), PageParams(page=3, per_page=10)
    )

    assert len(resp.data) == 5  # 25 - 20
    assert [h.age for h in resp.data] == list(range(20, 25))
    assert resp.has_prev is True
    assert resp.has_next is False


def test_exact_multiple_pages(backend: Backend) -> None:
    # 25 filas / 5 por página => exactamente 5 páginas; la última va llena.
    resp = paginate(
        backend.session, backend.select_all(), PageParams(page=5, per_page=5)
    )

    assert resp.total_pages == 5
    assert len(resp.data) == 5
    assert resp.has_next is False
    assert resp.has_prev is True


def test_count_respects_where_filter(backend: Backend) -> None:
    # age > 18 => edades 19..24 => 6 filas. El total NO debe ser 25.
    resp = paginate(
        backend.session, backend.select_age_gt(18), PageParams(page=1, per_page=100)
    )

    assert resp.total == 6
    assert resp.total_pages == 1
    assert [h.age for h in resp.data] == list(range(19, 25))


def test_filter_count_independent_of_page_size(backend: Backend) -> None:
    # Aunque la página sea pequeña, el total refleja el conjunto filtrado completo.
    resp = paginate(
        backend.session, backend.select_age_gt(18), PageParams(page=1, per_page=2)
    )

    assert resp.total == 6
    assert resp.total_pages == 3
    assert len(resp.data) == 2
    assert resp.has_next is True


def test_empty_result_set(backend: Backend) -> None:
    # Filtro que no matchea nada: sin ZeroDivisionError y metadata coherente.
    resp = paginate(
        backend.session, backend.select_age_gt(999), PageParams(page=1, per_page=10)
    )

    assert resp.total == 0
    assert resp.total_pages == 1
    assert resp.data == []
    assert resp.has_next is False
    assert resp.has_prev is False


def test_page_beyond_range(backend: Backend) -> None:
    # Página fuera de rango: data vacía pero total/total_pages siguen bien.
    resp = paginate(
        backend.session, backend.select_all(), PageParams(page=99, per_page=10)
    )

    assert resp.total == 25
    assert resp.total_pages == 3
    assert resp.data == []
    assert resp.has_next is False
    assert resp.has_prev is True


def test_items_are_model_instances(backend: Backend) -> None:
    # `.scalars()` debe devolver instancias del modelo, no Row/tuplas.
    resp = paginate(
        backend.session, backend.select_all(), PageParams(page=1, per_page=3)
    )

    assert len(resp.data) == 3
    assert all(isinstance(item, backend.model) for item in resp.data)
    assert not any(isinstance(item, tuple) for item in resp.data)


def test_metadata_echoes_params(backend: Backend) -> None:
    resp = paginate(
        backend.session, backend.select_all(), PageParams(page=2, per_page=7)
    )

    assert resp.page == 2
    assert resp.per_page == 7


# --- mapper ---------------------------------------------------------------


def test_mapper_transforms_every_item(backend: Backend) -> None:
    resp = paginate(
        backend.session,
        backend.select_all(),
        PageParams(page=1, per_page=5),
        mapper=lambda hero: hero.name.upper(),
    )

    assert resp.data == [f"H{i}" for i in range(5)]


def test_mapper_preserves_order(backend: Backend) -> None:
    resp = paginate(
        backend.session,
        backend.select_all(),
        PageParams(page=2, per_page=10),
        mapper=lambda hero: hero.age,
    )

    assert resp.data == list(range(10, 20))


def test_mapper_to_dataclass(backend: Backend) -> None:
    resp = paginate(
        backend.session,
        backend.select_all(),
        PageParams(page=1, per_page=3),
        mapper=lambda hero: HeroDTO(label=hero.name, age=hero.age),
    )

    assert resp.data == [HeroDTO(label=f"h{i}", age=i) for i in range(3)]
    assert all(isinstance(item, HeroDTO) for item in resp.data)


def test_mapper_to_pydantic_schema(backend: Backend) -> None:
    # Caso típico ORM -> schema de respuesta.
    resp = paginate(
        backend.session,
        backend.select_all(),
        PageParams(page=1, per_page=3),
        mapper=lambda hero: HeroSchema(label=hero.name, age=hero.age),
    )

    assert all(isinstance(item, HeroSchema) for item in resp.data)
    assert [item.label for item in resp.data] == [f"h{i}" for i in range(3)]
    assert resp.model_dump()["data"][0] == {"label": "h0", "age": 0}


def test_mapper_does_not_alter_metadata(backend: Backend) -> None:
    params = PageParams(page=2, per_page=10)

    plain = paginate(backend.session, backend.select_all(), params)
    mapped = paginate(
        backend.session, backend.select_all(), params, mapper=lambda hero: hero.age
    )

    assert mapped.total == plain.total
    assert mapped.total_pages == plain.total_pages
    assert mapped.page == plain.page
    assert mapped.per_page == plain.per_page
    assert mapped.has_next == plain.has_next
    assert mapped.has_prev == plain.has_prev


def test_mapper_only_applied_to_current_page(backend: Backend) -> None:
    # No debe invocarse sobre las 25 filas, solo sobre las 10 de la página.
    calls: list[int] = []

    def mapper(hero: object) -> int:
        age: int = hero.age  # ty:ignore[unresolved-attribute]
        calls.append(age)
        return age

    resp = paginate(
        backend.session,
        backend.select_all(),
        PageParams(page=1, per_page=10),
        mapper=mapper,
    )

    assert len(calls) == 10
    assert len(resp.data) == 10


def test_mapper_respects_where_filter(backend: Backend) -> None:
    resp = paginate(
        backend.session,
        backend.select_age_gt(18),
        PageParams(page=1, per_page=100),
        mapper=lambda hero: hero.age,
    )

    assert resp.total == 6
    assert resp.data == list(range(19, 25))


def test_mapper_not_called_on_empty_result_set(backend: Backend) -> None:
    calls: list[object] = []

    def mapper(hero: object) -> object:
        calls.append(hero)
        return hero

    resp = paginate(
        backend.session,
        backend.select_age_gt(999),
        PageParams(page=1, per_page=10),
        mapper=mapper,
    )

    assert calls == []
    assert resp.data == []
    assert resp.total == 0
    assert resp.total_pages == 1


def test_mapper_on_page_beyond_range(backend: Backend) -> None:
    resp = paginate(
        backend.session,
        backend.select_all(),
        PageParams(page=99, per_page=10),
        mapper=lambda hero: hero.name,
    )

    assert resp.data == []
    assert resp.total == 25
    assert resp.total_pages == 3
    assert resp.has_prev is True


def test_mapper_none_is_equivalent_to_omitting_it(backend: Backend) -> None:
    # Pasar `mapper=None` explícitamente (variable opcional propagada) no mapea.
    params = PageParams(page=1, per_page=5)

    resp = paginate(backend.session, backend.select_all(), params, mapper=None)

    assert all(isinstance(item, backend.model) for item in resp.data)
    assert [h.age for h in resp.data] == list(range(0, 5))
