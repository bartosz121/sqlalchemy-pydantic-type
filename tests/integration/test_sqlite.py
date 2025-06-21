from collections.abc import Generator
from typing import Any

import pytest
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Table, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from sqlalchemy_pydantic_type import BasePydanticType
from tests.conftest import Flag, UserMeta


class PydanticString(BasePydanticType):
    impl = String

    def _default_model_serializer(self, model: BaseModel) -> Any:  # noqa: PLR6301
        return model.model_dump_json()

    def _default_model_deserializer(self, value: Any) -> BaseModel:
        return self._pydantic_model_type.model_validate_json(value)


class Base(DeclarativeBase): ...


class UserSqlite(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    meta: Mapped[UserMeta] = mapped_column(PydanticString(UserMeta))


UserCoreTable = Table(
    "users_core",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String),
    Column("meta", PydanticString(UserMeta)),
)


@pytest.fixture(scope="function")
def sqlite_db() -> Generator[Session, Any, Any]:
    engine = create_engine("sqlite:///:memory:")
    UserSqlite.metadata.create_all(engine)
    sessionmaker_ = sessionmaker(bind=engine)
    session = sessionmaker_()
    yield session
    UserSqlite.metadata.drop_all(engine)
    session.close()


def test_sqlite_string(sqlite_db: Session):
    meta = UserMeta(
        flags=[
            Flag(name="f1", enabled=True),
            Flag(name="f1", enabled=False),
        ],
        login_count=42,
    )
    user = UserSqlite(name="user1", meta=meta)
    sqlite_db.add(user)
    sqlite_db.commit()

    loaded_user = sqlite_db.query(UserSqlite).first()
    assert loaded_user is not None
    assert isinstance(loaded_user.meta, UserMeta)
    assert loaded_user.meta.flags == meta.flags
    assert loaded_user.meta.login_count == meta.login_count


def test_sqlite_core_table(sqlite_db: Session):
    """New test for the Core-style class."""
    meta = UserMeta(
        flags=[
            Flag(name="admin", enabled=True),
            Flag(name="beta_tester", enabled=True),
        ],
        login_count=42,
    )

    insert_stmt = UserCoreTable.insert().values(name="core_user", meta=meta)
    sqlite_db.execute(insert_stmt)
    sqlite_db.commit()

    select_stmt = UserCoreTable.select()
    loaded_user = sqlite_db.execute(select_stmt).first()

    assert loaded_user is not None
    assert isinstance(loaded_user.meta, UserMeta)
    assert loaded_user.meta.flags == meta.flags
    assert loaded_user.meta.login_count == meta.login_count
