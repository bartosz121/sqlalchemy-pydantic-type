from collections.abc import Callable
from functools import cached_property
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, TypeAdapter
from sqlalchemy import Dialect
from sqlalchemy.types import TypeDecorator, TypeEngine

T = TypeVar("T")


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


class BaseTypeAdapterType(TypeDecorator[T], Generic[T]):
    """
    SQLAlchemy TypeDecorator for Pydantic TypeAdapter.

    Unlike BasePydanticType which requires a BaseModel class,
    this accepts a TypeAdapter directly, enabling support for
    dataclasses, TypedDicts, and other types.

    This class is generic over `T`, which enables type checking for custom
    serializer/deserializer callbacks. When subclassing, you can either:

    1. Specify the type parameter for strict typing:

    .. code-block:: python

        class ProfileJSON(BaseTypeAdapterType[UserProfile]):
            impl = JSON

    2. Use [Any] as the type parameter for a reusable class that works with any TypeAdapter:

    .. code-block:: python

        class TypeAdapterJSON(BaseTypeAdapterType[Any]):
            impl = JSON

        TypeAdapterJSON(TypeAdapter(UserProfile))
        TypeAdapterJSON(TypeAdapter(Config))
    """  # fmt: skip

    impl: TypeEngine[Any] | type[TypeEngine[Any]]
    cache_ok: bool | None

    _type_adapter: TypeAdapter[T]
    _serializer: Callable[[T], Any]
    _deserializer: Callable[[Any], T]

    def __init__(
        self,
        type_adapter: TypeAdapter[T],
        *args: Any,
        serializer: Callable[[T], Any] | None = None,
        deserializer: Callable[[Any], T] | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)

        self._type_adapter = type_adapter

        self._serializer = serializer or self._default_serializer
        self._deserializer = deserializer or self._default_deserializer

    @property
    def type_adapter(self) -> TypeAdapter[T]:
        return self._type_adapter

    def _default_serializer(self, value: T) -> Any:
        return self._type_adapter.dump_python(value, mode="json")

    def _default_deserializer(self, value: Any) -> T:
        return self._type_adapter.validate_python(value)

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine[Any]:
        impl = self.__class__.impl
        return dialect.type_descriptor(impl() if callable(impl) else impl)

    def process_bind_param(
        self,
        value: T | None,
        dialect: Dialect,
    ) -> Any:
        if value is None:
            return None

        return self._serializer(value)

    def process_result_value(
        self,
        value: Any | None,
        dialect: Dialect,
    ) -> T | None:
        if value is None:
            return None
        return self._deserializer(value)
