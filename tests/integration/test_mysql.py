# pyright: reportUnknownVariableType=false

import os
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import String, create_engine
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database  # pyright: ignore[reportMissingTypeStubs]

from sqlalchemy_pydantic_type import BasePydanticType
from tests.conftest import Flag, UserMeta


class PydanticJSON(BasePydanticType):
    impl = JSON


class Base(DeclarativeBase): ...


class UserMySQL(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(length=60))
    meta: Mapped[UserMeta] = mapped_column(PydanticJSON(UserMeta))


@pytest.fixture(scope="function")
def mysql_db() -> Generator[Session, Any, Any]:
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "test_user")
    password = os.getenv("MYSQL_PASSWORD", "test_password")
    db_name = os.getenv("MYSQL_DB", "test_db")

    db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_engine(db_url)

    if database_exists(db_url):
        drop_database(db_url)

    create_database(db_url)

    UserMySQL.metadata.create_all(engine)

    sessionmaker_ = sessionmaker(bind=engine)

    with sessionmaker_() as session:
        yield session

    engine.dispose()
    drop_database(db_url)


def test_mysql_json(mysql_db: Session):
    meta = UserMeta(
        flags=[
            Flag(name="f1", enabled=True),
            Flag(name="f2", enabled=False),
        ],
        login_count=42,
    )
    user = UserMySQL(name="user1", meta=meta)
    mysql_db.add(user)
    mysql_db.commit()

    loaded_user = mysql_db.query(UserMySQL).first()
    assert loaded_user is not None
    assert isinstance(loaded_user.meta, UserMeta)
    assert loaded_user.meta.flags == meta.flags
    assert loaded_user.meta.login_count == meta.login_count
