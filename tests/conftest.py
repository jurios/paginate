"""Fixture `backend`, parametrizado por ORM.

Cada test se ejecuta dos veces (SQLAlchemy y SQLModel). Los modelos y el
dataclass Backend viven en `factories.py`, NO aquí, para no importar desde
conftest desde los módulos de test.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy import select as sa_select
from sqlalchemy.orm import Session as SASession
from sqlmodel import Session as SMSession
from sqlmodel import SQLModel, col
from sqlmodel import select as sm_select

from tests.factories import SEED_SIZE, Backend, HeroSA, HeroSM, SABase


@pytest.fixture(params=["sqlalchemy", "sqlmodel"])
def backend(request: pytest.FixtureRequest) -> Iterator[Backend]:
    engine = create_engine("sqlite://")

    if request.param == "sqlalchemy":
        SABase.metadata.create_all(engine)
        with SASession(engine) as session:
            session.add_all([HeroSA(name=f"h{i}", age=i) for i in range(SEED_SIZE)])
            session.commit()
            yield Backend(
                name="sqlalchemy",
                session=session,
                model=HeroSA,
                select_all=lambda: sa_select(HeroSA).order_by(HeroSA.id),
                select_age_gt=lambda n: (
                    sa_select(HeroSA).where(HeroSA.age > n).order_by(HeroSA.id)
                ),
            )
    else:
        SQLModel.metadata.create_all(engine)
        with SMSession(engine) as session:
            session.add_all([HeroSM(name=f"h{i}", age=i) for i in range(SEED_SIZE)])
            session.commit()
            yield Backend(
                name="sqlmodel",
                session=session,
                model=HeroSM,
                select_all=lambda: sm_select(HeroSM).order_by(col(HeroSM.id)),
                select_age_gt=lambda n: (
                    sm_select(HeroSM).where(HeroSM.age > n).order_by(col(HeroSM.id))
                ),
            )
