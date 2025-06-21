# SQLAlchemy Pydantic Type

**SQLAlchemy Pydantic Type** is a Python package that bridges SQLAlchemy and Pydantic by providing a custom SQLAlchemy type for seamless serialization and deserialization of Pydantic models as database column values.

The main goal of this project is to make it easy to store and retrieve complex data structures (such as JSON fields) as Pydantic models in your database tables, with automatic conversion between Python objects and database representations. This is especially useful for APIs or applications where you want strong data validation and type safety using Pydantic, while leveraging SQLAlchemy's ORM capabilities.

For example, if you have an `Event` table with a `meta` column of type JSON, you can use `BasePydanticType` to ensure that when you save a Pydantic model to the database, it is automatically serialized to JSON, and when you load it, it is deserialized back into your Pydantic model. The serialization/deserialization logic can be customized by overriding methods or passing custom callables.

See the [examples](examples/) directory for real-world usage.

## Features

- **Automatic serialization/deserialization** of Pydantic models to/from database columns (e.g., JSON, String).
- **Customizable serialization**: Override methods or provide custom serializer/deserializer functions.
- **Easy integration** with SQLAlchemy ORM and Core.
- **Type safety**: Ensures your database fields are always valid Pydantic models.
- **Alembic support**: Includes helpers for proper autogeneration of migration scripts.

## Example

Here's how you can create a custom type that serializes Pydantic models to and from JSON strings:

```python
from sqlalchemy_pydantic_type import BasePydanticType
from sqlalchemy import String
from pydantic import BaseModel

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
