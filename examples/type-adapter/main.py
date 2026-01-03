# ruff: noqa: S101, PLR2004
"""
Example: Using BaseTypeAdapterType with TypedDict

This example demonstrates how to use BaseTypeAdapterType to store
Python TypedDicts in a SQLite database. This is useful when you want
type-safety for structured data without the complexity of full Pydantic models.
"""

from typing import Any, TypedDict

from pydantic import TypeAdapter
from sqlalchemy import JSON, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from sqlalchemy_pydantic_type import BaseTypeAdapterType


# 1. Define a TypedDict for our structured data
class Dimensions(TypedDict):
    width: float
    height: float
    depth: float
    unit: str


# 2. Create a TypeAdapter for the TypedDict
dimensions_adapter = TypeAdapter(Dimensions)


# 3. Define a SQLAlchemy type using BaseTypeAdapterType
class DimensionsJSON(BaseTypeAdapterType[Dimensions]):
    """Stores Dimensions as JSON in the database"""

    impl = JSON
    cache_ok = True


# Option: Reusable version - use `Any` to work with any TypeAdapter
# This allows using the same class for different columns/types.
class ReusableJSON(BaseTypeAdapterType[Any]):
    impl = JSON
    cache_ok = True


# 4. Set up SQLAlchemy Model
class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    # Use our custom DimensionsJSON type
    dimensions: Mapped[Dimensions] = mapped_column(DimensionsJSON(dimensions_adapter))


def main():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # 5. Create products
        products = [
            Product(
                name="Coffee Table",
                dimensions={"width": 120, "height": 45, "depth": 60, "unit": "cm"},
            ),
            Product(
                name="Bookshelf",
                dimensions={"width": 80, "height": 180, "depth": 30, "unit": "cm"},
            ),
        ]
        session.add_all(products)
        session.commit()

        # 6. Query and verify
        stmt = select(Product).order_by(Product.name)
        loaded_products = session.scalars(stmt).all()

        print(f"Loaded {len(loaded_products)} products:")
        for p in loaded_products:
            # (variable) dims: Dimensions
            dims = p.dimensions

            # `dims` keys are type safe
            print(f"- {p.name}: {dims['width']}x{dims['height']} {dims['unit']}")

        assert len(loaded_products) == 2
        assert loaded_products[0].name == "Bookshelf"
        assert isinstance(loaded_products[0].dimensions, dict)


if __name__ == "__main__":
    main()
