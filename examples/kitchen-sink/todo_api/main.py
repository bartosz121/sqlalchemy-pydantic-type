from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Any, TypedDict

from fastapi import APIRouter, BackgroundTasks, Depends, FastAPI, Query
from fastapi.requests import Request
from pydantic import BaseModel
from sqlalchemy import JSON, String, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.types import ASGIApp, Receive, Scope, Send

from sqlalchemy_pydantic_type import BasePydanticType


# Database Setup and Models
class Base(DeclarativeBase): ...


class PydanticJSON(BasePydanticType):
    impl = JSON


class PydanticString(BasePydanticType):
    """
    A Pydantic type with custom `_default_model_serializer` and `default_model_deserializer`
    that serializes and deserializes Pydantic models to and from JSON strings.
    """

    impl = String
    cache_ok = True

    def _default_model_serializer(self, model: BaseModel) -> Any:
        return model.model_dump_json()

    def _default_model_deserializer(self, value: Any | None) -> BaseModel:
        assert isinstance(value, str)
        return self._pydantic_model_type.model_validate_json(value)


class AuditMeta(BaseModel):
    path: str
    method: str
    action: str


class TodoDb(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    completed: Mapped[bool] = mapped_column(default=False)


class AuditDb(Base):
    """
    meta_string is a PydanticString type that serializes the AuditMeta model to a JSON string and deserializes it back
    meta_json is a PydanticJSON type that serializes the AuditMeta model to a JSON object and deserializes it back
    """

    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(primary_key=True)
    meta_string: Mapped[AuditMeta] = mapped_column(PydanticString(AuditMeta))
    meta_json: Mapped[AuditMeta] = mapped_column(PydanticJSON(AuditMeta))
    timestamp: Mapped[str] = mapped_column(default=lambda: datetime.now(timezone.utc))


# Middleware for Audit Logging
class AuditMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        try:
            audit_meta = AuditMeta(
                path=scope["path"],
                method=scope["method"],
                action="request",
            )
            audit = AuditDb(meta_string=audit_meta, meta_json=audit_meta)
            sessionmaker: async_sessionmaker[AsyncSession] = scope["state"]["sessionmaker"]

            async with sessionmaker() as session:
                session.add(audit)
                await session.commit()

        except Exception as e:
            print(f"Error logging audit: {e}")

        await self.app(scope, receive, send)


# Background Tasks
async def task_add_todo_created_audit(
    sessionmaker: async_sessionmaker[AsyncSession],
    todo_id: int,
):
    async with sessionmaker() as session:
        try:
            audit_meta = AuditMeta(
                path="/todo",
                method="POST",
                action=f"created_{todo_id}",
            )
            audit = AuditDb(meta_string=audit_meta, meta_json=audit_meta)
            session.add(audit)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Error logging audit for todo {todo_id}: {e}")


# Application State and Lifespan
class State(TypedDict):
    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[State]:  # noqa: RUF029
    engine = create_async_engine("sqlite+aiosqlite:///todo.db", echo=True)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield {
        "engine": engine,
        "sessionmaker": sessionmaker,
    }


# Dependency Injection for Database Session
async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = request.state.sessionmaker
    async with sessionmaker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            print(f"Error in session: {e}")
        finally:
            await session.close()


DbSession = Annotated[AsyncSession, Depends(get_session)]


# API Routes for Todos
todo_router = APIRouter()


class TodoRead(BaseModel):
    id: int
    title: str
    completed: bool


@todo_router.get("/todo")
async def get_todos(session: DbSession):
    todos = (await session.execute(select(TodoDb))).scalars().all()
    return todos


class TodoCreate(BaseModel):
    title: str
    completed: bool = False


@todo_router.post("/todo", response_model=TodoRead)
async def create_todo(request: Request, data: TodoCreate, session: DbSession, background_tasks: BackgroundTasks):
    todo = TodoDb(
        title=data.title,
        completed=data.completed,
    )
    session.add(todo)
    await session.commit()
    await session.refresh(todo)

    background_tasks.add_task(
        task_add_todo_created_audit,
        request.state.sessionmaker,
        todo.id,
    )
    return todo


# API Routes for Audits
audit_router = APIRouter()


@audit_router.get("/audit")
async def get_audits(session: DbSession, meta_method: Annotated[str | None, Query()] = None):
    audits = (await session.execute(select(AuditDb))).scalars().all()

    # `meta` is automatically serialized to pydantic AuditMeta model
    if len(audits) > 0:
        print(f"\t{audits[0].meta_string=}")
        print(f"\t{audits[0].meta_json=}")

    if meta_method:
        audits = [audit for audit in audits if audit.meta_string.method == meta_method]

    return audits


# Application Factory
def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan, debug=True)

    app.add_middleware(AuditMiddleware)

    app.include_router(todo_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")

    return app
