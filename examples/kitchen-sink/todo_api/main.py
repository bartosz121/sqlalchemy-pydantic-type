"""
FastAPI app demonstrating sqlalchemy-pydantic-type with Alembic migrations.

- BasePydanticType: In POST /users/{user_id}/projects, user.profile is automatically
  deserialized into a UserProfile instance, allowing direct method calls like
  get_max_projects() without manual conversion
- Alembic: render_item configuration in migrations/env.py for autogenerate support
"""

from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import JSON, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_pydantic_type import BasePydanticType


# 1. Pydantic Model for our structured data
class UserProfile(BaseModel):
    theme: str = "light"
    notifications: bool = True
    plan: Literal["free", "pro"] = "free"

    def get_max_projects(self) -> int:
        return 2 if self.plan == "free" else 100


# Model for partial updates (PATCH)
class UserProfileUpdate(BaseModel):
    theme: str | None = None
    notifications: bool | None = None
    plan: Literal["free", "pro"] | None = None


# Models for API Request/Response
class UserCreate(BaseModel):
    username: str
    profile: UserProfile = UserProfile()


class UserRead(BaseModel):
    id: int
    username: str
    profile: UserProfile
    project_count: int

    class Config:
        from_attributes = True


# 2. Custom SQLAlchemy Type using BasePydanticType
class PydanticJSON(BasePydanticType):
    """Serializes/deserializes Pydantic models as JSON."""

    impl = JSON
    cache_ok = True


# 3. SQLAlchemy Model using the custom type
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    project_count: Mapped[int] = mapped_column(default=0)
    # The Pydantic model is automatically handled by PydanticJSON
    profile: Mapped[UserProfile] = mapped_column(PydanticJSON(UserProfile))


# 4. Database Configuration
engine = create_async_engine("sqlite+aiosqlite:///todo.db")
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with SessionLocal() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]

# 5. FastAPI Application
app = FastAPI(title="Kitchen Sink")


@app.post("/users", response_model=UserRead)
async def create_user(data: UserCreate, db: DbSession):
    user = User(username=data.username, profile=data.profile)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.get("/users/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: DbSession):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/users", response_model=list[UserRead])
async def list_users(db: DbSession):
    result = await db.execute(select(User))
    return result.scalars().all()


@app.patch("/users/{user_id}/profile", response_model=UserRead)
async def update_profile(user_id: int, profile_update: UserProfileUpdate, db: DbSession):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = profile_update.model_dump(exclude_unset=True)
    user.profile = user.profile.model_copy(update=update_data)

    await db.commit()
    await db.refresh(user)
    return user


@app.post("/users/{user_id}/projects", response_model=UserRead)
async def create_project(user_id: int, db: DbSession):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # `user.profile` a pydantic model instance retrieved directly from the database,
    # allowing us to call its methods (like `get_max_projects`)
    if user.project_count >= user.profile.get_max_projects():
        raise HTTPException(status_code=403, detail=f"Limit reached for {user.profile.plan} plan. Upgrade to 'pro'!")

    user.project_count += 1
    await db.commit()
    await db.refresh(user)
    return user
