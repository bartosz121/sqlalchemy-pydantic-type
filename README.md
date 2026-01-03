# SQLAlchemy Pydantic Type

![License](https://img.shields.io/github/license/bartosz121/sqlalchemy-pydantic-type)
![Build](https://img.shields.io/github/actions/workflow/status/bartosz121/sqlalchemy-pydantic-type/build.yml)
![Codecov](https://img.shields.io/codecov/c/github/bartosz121/sqlalchemy-pydantic-type)
![PyPI Version](https://img.shields.io/pypi/v/sqlalchemy-pydantic-type)
![Python Version](https://img.shields.io/pypi/pyversions/sqlalchemy-pydantic-type)

**SQLAlchemy Pydantic Type** is a Python package that bridges SQLAlchemy and Pydantic by providing a custom SQLAlchemy type for automatic serialization and deserialization of Pydantic models as database column values.

The main goal of this project is to make it easy to store and retrieve complex data structures (such as JSON fields) as Pydantic models in your SQLAlchemy 2.0 ORM models, with automatic conversion between Python objects and database representations.

See the [examples](examples/) directory for real-world usage.

## Example

### Using `BasePydanticType` with Pydantic models

Use `BasePydanticType` when your data is defined as a Pydantic `BaseModel`:

```python
from typing import Any

from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_pydantic_type import BasePydanticType


class Base(DeclarativeBase):
    pass


class PydanticString(BasePydanticType):
    """
    Custom type that serializes Pydantic models to JSON strings and
    deserializes JSON strings back into Pydantic models.
    """
    impl = String
    cache_ok = True

    def _default_model_serializer(self, model: BaseModel) -> Any:
        return model.model_dump_json()

    def _default_model_deserializer(self, value: Any | None) -> BaseModel:
        return self._pydantic_model_type.model_validate_json(value)


class UserMeta(BaseModel):
    roles: list[str]
    is_active: bool


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    meta: Mapped[UserMeta] = mapped_column(PydanticString(UserMeta))
```

In this example, the `meta` column will automatically handle conversion between `UserMeta` Pydantic objects and JSON strings in the database.

### Using `BaseTypeAdapterType` with dataclasses and other types

Use `BaseTypeAdapterType` when your data is defined as a dataclass, `TypedDict`, or any other type supported by Pydantic's `TypeAdapter`:

```python
from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_pydantic_type import BaseTypeAdapterType


class Base(DeclarativeBase):
    pass


@dataclass
class Address:
    street: str
    city: str


@dataclass
class UserProfile:
    name: str
    age: int
    address: Address


# Create a TypeAdapter for the dataclass
user_profile_adapter = TypeAdapter(UserProfile)


# Option 1: Specify the exact type
class UserProfileJSON(BaseTypeAdapterType[UserProfile]):
    impl = JSON
    cache_ok = True


# Option 2: Reusable version - use `Any` to work with any TypeAdapter
class TypeAdapterJSON(BaseTypeAdapterType[Any]):
    impl = JSON
    cache_ok = True


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    profile: Mapped[UserProfile] = mapped_column(UserProfileJSON(user_profile_adapter))
```

In this example, the `profile` column stores a Python dataclass as JSON in the database, with automatic serialization and deserialization.

## Alembic Support

To enable proper migration script generation when using SQLAlchemy Pydantic Type with Alembic, follow these steps:

1. Install the package with Alembic support:
    ```bash
    pip install sqlalchemy_pydantic_type[alembic]
    ```

2. In your Alembic environment (`env.py`), import the `render_item` function:
    ```python
    from sqlalchemy_pydantic_type.alembic import render_item
    ```

3. Add the `render_item` argument to all `context.configure()` calls:
    ```python
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        render_item=render_item,  # Add this line
        dialect_opts={"paramstyle": "named"},
    )
    ```

This ensures that Alembic correctly generates migration scripts for columns using Pydantic types.

For a complete working example, check out the [kitchen sink example](examples/kitchen_sink) in the examples directory.

## Development

For details on setting up the development environment and contributing, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

This package was created with [The Hatchlor] project template.

[The Hatchlor]: https://github.com/bartosz121/the-hatchlor
[hatch]: https://hatch.pypa.io/
