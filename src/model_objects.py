from __future__ import annotations

from collections.abc import Mapping
from enum import Enum


class Product:
    def __init__(self, name: str, unit: ProductUnit) -> None:
        self.name = name
        self.unit = unit


class ProductQuantity:
    def __init__(self, product: Product, quantity: float) -> None:
        self.product = product
        self.quantity = quantity


class ProductUnit(Enum):
    EACH = 1
    KILO = 2


class SpecialOfferType(Enum):
    THREE_FOR_TWO = 1
    TEN_PERCENT_DISCOUNT = 2
    TWO_FOR_AMOUNT = 3
    FIVE_FOR_AMOUNT = 4


class Offer:
    def __init__(
        self,
        offer_type: SpecialOfferType,
        product: Product,
        argument: float,
    ) -> None:
        self.offer_type = offer_type
        self.product = product
        self.argument = argument


class Discount:
    def __init__(
        self,
        product: Product,
        description: str,
        discount_amount: float,
    ) -> None:
        self.product = product
        self.description = description
        self.discount_amount = discount_amount


class Combo:
    """Define produtos e quantidades de um combo com desconto fixo de 10%.

    O percentual é fixo porque a nova regra de negócio do trabalho determina 10%.
    Use os mesmos objetos Product do catálogo e do carrinho, pois o legado os agrupa
    como chaves por identidade.
    """

    discount_percentage = 10.0

    def __init__(
        self,
        name: str,
        required_quantities: Mapping[Product, float],
    ) -> None:
        if not name.strip():
            raise ValueError("O combo precisa ter um nome.")
        if not required_quantities:
            raise ValueError("O combo precisa conter ao menos um produto.")
        if any(quantity <= 0 for quantity in required_quantities.values()):
            raise ValueError("As quantidades exigidas pelo combo devem ser positivas.")

        self.name = name
        self.required_quantities = dict(required_quantities)
