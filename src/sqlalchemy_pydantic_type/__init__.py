from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sqlalchemy-pydantic-type")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError


from sqlalchemy_pydantic_type.core import BasePydanticType

__all__ = [
    "BasePydanticType",
    "__version__",
]
