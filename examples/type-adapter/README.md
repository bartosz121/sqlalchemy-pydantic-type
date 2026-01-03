# Type Adapter: Dataclasses & TypedDicts

Example demonstrating `BaseTypeAdapterType` for types beyond Pydantic models, such as `TypedDict`.

## Structure
- `main.py`: Implementation showing `TypedDict` serialization in a SQLite database.

## Setup
```bash
uv run python main.py
```

## Integration Details

### TypedDict support
`BaseTypeAdapterType` allows using any type supported by Pydantic's `TypeAdapter`. This example uses `TypedDict` for structured product dimensions:

```python
# dimensions is automatically deserialized into a dictionary with checked keys
dims = p.dimensions
print(f"{dims['width']}x{dims['height']} {dims['unit']}")
```

### Reusable types
You can define a reusable type by using `Any` as the generic parameter, allowing the same SQLAlchemy type class to handle different `TypeAdapter` instances:

```python
class ReusableJSON(BaseTypeAdapterType[Any]):
    impl = JSON
```
