# pyright: reportPrivateUsage=false

from typing import Any
from unittest.mock import Mock

from pydantic import BaseModel
from sqlalchemy import JSON, Dialect, String

from sqlalchemy_pydantic_type import BasePydanticType
from tests.conftest import Flag, UserMeta


class PydanticJSON(BasePydanticType):
    impl = JSON
    cache_ok = True


class PydanticString(BasePydanticType):
    impl = String
    cache_ok = True

    def _default_model_serializer(self, model: BaseModel) -> str:  # noqa: PLR6301
        return model.model_dump_json()

    def _default_model_deserializer(self, value: Any) -> BaseModel:
        return self._pydantic_model_type.model_validate_json(value)


def test_initialization():
    serializer = Mock()
    deserializer = Mock()
    pydantic_type = PydanticJSON(
        UserMeta,
        serializer=serializer,
        deserializer=deserializer,
    )
    assert pydantic_type._pydantic_model_type == UserMeta
    assert pydantic_type._model_serializer == serializer
    assert pydantic_type._model_deserializer == deserializer


def test_default_serializer():
    pydantic_type = PydanticJSON(UserMeta)
    model = UserMeta(login_count=1, flags=[Flag(name="f1", enabled=True)])
    serialized = pydantic_type._default_model_serializer(model)
    assert serialized == {"login_count": 1, "flags": [{"name": "f1", "enabled": True}]}


def test_default_deserializer():
    pydantic_type = PydanticJSON(UserMeta)
    flags = [
        {"name": "f1", "enabled": True},
    ]
    deserialized = pydantic_type._default_model_deserializer(
        {
            "login_count": 1,
            "flags": flags,
        }
    )
    assert isinstance(deserialized, UserMeta)
    assert deserialized.login_count == 1
    assert deserialized.flags == [Flag(name="f1", enabled=True)]


def test_type_adapter():
    pydantic_type = PydanticJSON(UserMeta)
    adapter = pydantic_type.type_adapter
    assert adapter.validate_python(
        {
            "login_count": 1,
            "flags": [
                {"name": "f1", "enabled": True},
            ],
        }
    ) == UserMeta(
        login_count=1,
        flags=[Flag(name="f1", enabled=True)],
    )


def test_process_bind_param():
    pydantic_type = PydanticJSON(UserMeta)
    model = UserMeta(
        login_count=1,
        flags=[Flag(name="f1", enabled=True)],
    )
    result = pydantic_type.process_bind_param(model, Mock(spec=Dialect))
    assert result == {"login_count": 1, "flags": [{"name": "f1", "enabled": True}]}


def test_process_result_value():
    pydantic_type = PydanticJSON(UserMeta)
    result = pydantic_type.process_result_value(
        {"login_count": 1, "flags": [{"name": "f1", "enabled": True}]}, Mock(spec=Dialect)
    )
    assert isinstance(result, UserMeta)
    assert result.login_count == 1
    assert result.flags == [Flag(name="f1", enabled=True)]


def test_load_dialect_impl():
    mock_dialect = Mock(spec=Dialect)
    mock_type_engine = Mock()
    PydanticJSON.impl = mock_type_engine
    pydantic_type = PydanticJSON(UserMeta)
    result = pydantic_type.load_dialect_impl(mock_dialect)
    mock_dialect.type_descriptor.assert_called_once_with(mock_type_engine())
    assert result == mock_dialect.type_descriptor.return_value
