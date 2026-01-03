from typing import Any

from sqlalchemy_pydantic_type.core import BasePydanticType, BaseTypeAdapterType

try:
    from alembic.autogenerate.api import AutogenContext
    from alembic.autogenerate.render import (
        _repr_type,  # pyright: ignore [reportPrivateUsage, reportUnknownVariableType]  # noqa: PLC2701
    )
except ImportError as e:
    msg = "The `alembic` package is required to use this module. Install it with: pip install sqla_orm_pydantic_type[alembic]"  # noqa: E501
    raise ImportError(msg) from e


def render_item(type_: str, obj: Any, autogen_context: AutogenContext):
    """
    Apply custom rendering for instances of `BasePydanticType` and `BaseTypeAdapterType`
    """

    if type_ == "type" and isinstance(obj, (BasePydanticType, BaseTypeAdapterType)):
        return _repr_type(obj.impl_instance, autogen_context)

    # default rendering for others
    return False
