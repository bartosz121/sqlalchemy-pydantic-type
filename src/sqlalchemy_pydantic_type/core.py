from collections.abc import Callable
from functools import cached_property
from typing import Any

from pydantic import BaseModel, TypeAdapter
from sqlalchemy import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine


class BasePydanticType(TypeDecorator[BaseModel]):
    impl: TypeEngine[Any] | type[TypeEngine[Any]]
    cache_ok: bool | None

    _pydantic_model_type: type[BaseModel]
    _model_serializer: Callable[[BaseModel], Any]
    _model_deserializer: Callable[[Any | None], BaseModel]

    def __init__(
        self,
        pydantic_model_type: type[BaseModel],
        *args: Any,
        serializer: Callable[[BaseModel], Any] | None = None,
        deserializer: Callable[[Any], BaseModel] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        self._pydantic_model_type = pydantic_model_type

        self._model_serializer = serializer or self._default_model_serializer
        self._model_deserializer = deserializer or self._default_model_deserializer

    @cached_property
    def type_adapter(self) -> TypeAdapter[BaseModel]:
        return TypeAdapter(self._pydantic_model_type)

    def _default_model_serializer(self, model: BaseModel) -> Any:  # noqa: PLR6301
        return model.model_dump(mode="json")

    def _default_model_deserializer(self, value: Any | None) -> BaseModel:
        return self.type_adapter.validate_python(value)

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        impl = self.__class__.impl
        return dialect.type_descriptor(impl() if callable(impl) else impl)

    def process_bind_param(
        self,
        value: BaseModel | None,
        dialect: Dialect,
    ) -> Any:
        if value is None:
            return None

        return self._model_serializer(value)

    def process_result_value(
        self,
        value: Any | None,
        dialect: Dialect,
    ) -> BaseModel | None:
        if value is None:
            return None
        return self._model_deserializer(value)
