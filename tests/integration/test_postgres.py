# pyright: reportUnknownVariableType=false

import os
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database  # pyright: ignore[reportMissingTypeStubs]

from sqlalchemy_pydantic_type import BasePydanticType
from tests.conftest import Flag, UserMeta


class PydanticJSONB(BasePydanticType):
    impl = JSONB


class Base(DeclarativeBase): ...


class UserPostgres(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    meta: Mapped[UserMeta] = mapped_column(PydanticJSONB(UserMeta))


@pytest.fixture(scope="function")
def postgres_db() -> Generator[Session, Any, Any]:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "test_user")
    password = os.getenv("POSTGRES_PASSWORD", "test_password")
    db_name = os.getenv("POSTGRES_DB", "test_db")

    db_url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_engine(db_url)

    if database_exists(db_url):
        drop_database(db_url)

    create_database(db_url)

    UserPostgres.metadata.create_all(engine)

    sessionmaker_ = sessionmaker(bind=engine)

    with sessionmaker_() as session:
        yield session

    drop_database(db_url)


def test_postgres_jsonb(postgres_db: Session):
    meta = UserMeta(
        flags=[
            Flag(name="f1", enabled=True),
            Flag(name="f2", enabled=False),
        ],
        login_count=42,
    )
    user = UserPostgres(name="user1", meta=meta)
    postgres_db.add(user)

    loaded_user = postgres_db.query(UserPostgres).first()
    assert loaded_user is not None
    assert isinstance(loaded_user.meta, UserMeta)
    assert loaded_user.meta.flags == meta.flags
    assert loaded_user.meta.login_count == meta.login_count
