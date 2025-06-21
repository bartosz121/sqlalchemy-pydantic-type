from pydantic import BaseModel


class Flag(BaseModel):
    name: str
    enabled: bool


class UserMeta(BaseModel):
    flags: list[Flag]
    login_count: int
