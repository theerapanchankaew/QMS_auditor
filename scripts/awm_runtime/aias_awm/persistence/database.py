from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.pool import StaticPool

from .tables import metadata


class Database:
    """SQLAlchemy database facade.

    Production target: PostgreSQL, e.g.
      postgresql+psycopg://user:pass@host:5432/aias

    Tests may use SQLite while exercising the same repository contracts.
    """

    def __init__(self, url: str, *, echo: bool = False) -> None:
        kwargs = {"echo": echo, "future": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in url:
                kwargs["poolclass"] = StaticPool
        self.engine: Engine = create_engine(url, **kwargs)

    def create_schema(self) -> None:
        # Import extension tables before create_all so the complete AWM schema is registered.
        from . import source_tables as _source_tables  # noqa: F401
        from . import temporal_tables as _temporal_tables  # noqa: F401
        from . import planning_tables as _planning_tables  # noqa: F401
        metadata.create_all(self.engine)

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        with self.engine.begin() as conn:
            yield conn
