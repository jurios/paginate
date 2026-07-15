from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlmodel import Field, SQLModel

SEED_SIZE = 25  # heroes con edades 0..24


class SABase(DeclarativeBase):
    pass


class HeroSA(SABase):
    __tablename__ = "hero_sa"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    age: Mapped[int] = mapped_column()


class HeroSM(SQLModel, table=True):
    __tablename__ = "hero_sm"
    id: int | None = Field(default=None, primary_key=True)
    name: str = ""
    age: int = 0


@dataclasses.dataclass
class Backend:
    name: str
    session: Any
    model: type
    select_all: Callable[[], Any]  # SELECT * ORDER BY id
    select_age_gt: Callable[[int], Any]  # SELECT * WHERE age > n ORDER BY id
