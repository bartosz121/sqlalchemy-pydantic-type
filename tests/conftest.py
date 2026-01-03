from dataclasses import dataclass

from pydantic import BaseModel


class Flag(BaseModel):
    name: str
    enabled: bool


class UserMeta(BaseModel):
    flags: list[Flag]
    login_count: int


@dataclass
class Permission:
    name: str
    level: int


@dataclass
class UserSettings:
    permissions: list[Permission]
    theme: str
