# Kitchen Sink: FastAPI & Alembic

A FastAPI implementation demonstrating `BasePydanticType` usage and Alembic migration support.

## Structure
- `todo_api/main.py`: Application logic and database models.
- `migrations/env.py`: Alembic configuration using `render_item`.

## Setup
```bash
uv run alembic upgrade head
uv run uvicorn todo_api.main:app --reload
```

## Integration Details

### Pydantic model usage
In `POST /users/{user_id}/projects`, the `user.profile` is automatically deserialized into a `UserProfile` instance when fetched from the database. This allows calling methods like `get_max_projects()` directly without any manual Pydantic validation or conversion in the endpoint code:

```python
# No manual instantiation needed; user.profile is already a UserProfile object
if user.project_count >= user.profile.get_max_projects():
    raise HTTPException(status_code=403)
```

### Alembic support
Custom types are rendered in migrations via `render_item` in `migrations/env.py`. This enables `alembic revision --autogenerate` to correctly identify and script Pydantic columns.
