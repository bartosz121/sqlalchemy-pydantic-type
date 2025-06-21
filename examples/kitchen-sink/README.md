# Kitchen Sink Example for `sqla-orm-pydantic-type`

This project is an example demonstrating how to use the `sqla-orm-pydantic-type` package in a real-world application.

## What the App Does

This example implements a Todo API with an `AuditMiddleware`. The middleware logs HTTP requests to an `audits` table in the database. The `audits` table has a `meta_string` and `meta_json` fields, which are represented in Python as a Pydantic model (`AuditMeta`) but stored in the database as a string(`meta_string`) and json(`meta_json`). This is achieved using the `sqla-orm-pydantic-type` package and the `PydanticString` and `PydanticJSON` classes.

### Key Features

- **Automatic Conversion**: When retrieving audit records from the database, the `meta_string` and `meta_json` fields are automatically converted back into `AuditMeta` Pydantic model
- **Query Filtering**: For example, in the `GET /api/v1/audit` endpoint, you can filter audit records based on the `meta_string.method` field using a query parameter. This is possible because the `meta_string` field is deserialized into a Pydantic model when fetched from the database.

## Getting Started

1. Run database migrations:

   ```bash
   uv run alembic upgrade head
   ```

2. Start application

    ```bash
   uv run uvicorn --workers 1 --factory todo_api.main:create_app --host 0.0.0.0 --port 8000 --reload
   ```

3. Open your browser and navigate to the FastAPI docs at http://127.0.0.1:8000/docs.

4. Do the following:

    - Use the POST /api/v1/todo endpoint to create a new todo
    - Use the GET /api/v1/todo endpoint to retrieve todos
    - Now that you have few entries in `audit` table, you can use `/audits` GET endpoint to look through them and use `meta_method` query parameter which you can use to filter `AuditDb` items with. Because `AuditDb.meta_string` is serialized from string back to pydantic `AuditMeta` model we can filter items like this: `[audit for audit in audits if audit.meta_string.method == meta_method]`
