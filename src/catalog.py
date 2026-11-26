from __future__ import annotations

from interfaces import CatalogReaderPort, CatalogWriterPort
from model_objects import Product


class SupermarketCatalog(CatalogReaderPort, CatalogWriterPort):

    def add_product(self, product: Product, price: float) -> None:
        raise Exception("cannot be called from a unit test - it accesses the database")

    def unit_price(self, product: Product) -> float:
        raise Exception("cannot be called from a unit test - it accesses the database")

    def product_by_name(self, name: str) -> Product | None:
        raise Exception("cannot be called from a unit test - it accesses the database")

