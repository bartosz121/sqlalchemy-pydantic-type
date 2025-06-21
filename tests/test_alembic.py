import pytest
from alembic.autogenerate.api import AutogenContext
from alembic.migration import MigrationContext
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import default
from sqlalchemy.types import String

from sqlalchemy_pydantic_type import BasePydanticType
from sqlalchemy_pydantic_type.alembic import render_item
from tests.conftest import UserMeta

migration_context = MigrationContext.configure(dialect=default.DefaultDialect())


@pytest.fixture
def autogen_context() -> AutogenContext:
    ctx = AutogenContext(migration_context)
    ctx.opts.update({"render_item": render_item, "sqlalchemy_module_prefix": "sa."})
    return ctx


def test_render_item_with_postgresql_jsonb(autogen_context: AutogenContext):
    class PydanticJSONB(BasePydanticType):
        impl = JSONB

    postgres_jsonb_type = PydanticJSONB(UserMeta)
    postgres_jsonb_type_item = render_item("type", postgres_jsonb_type, autogen_context)
    assert postgres_jsonb_type_item == "postgresql.JSONB(astext_type=Text())"


def test_render_item_with_mysql_json(autogen_context: AutogenContext):
    class PydanticMySQLJSON(BasePydanticType):
        impl = JSON

    mysql_json_type = PydanticMySQLJSON(UserMeta)
    mysql_json_type_item = render_item("type", mysql_json_type, autogen_context)
    assert mysql_json_type_item == "mysql.JSON()"


def test_render_item_with_string_type(autogen_context: AutogenContext):
    class PydanticString(BasePydanticType):
        impl = String

    string_type = PydanticString(UserMeta)
    string_type_item = render_item("type", string_type, autogen_context)
    assert string_type_item == "sa.String()"
