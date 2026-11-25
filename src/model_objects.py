from __future__ import annotations

from collections.abc import Mapping
from enum import Enum


class Product:
    """Produto vendido. Comparado por identidade: o carrinho e as ofertas o usam como chave."""

    def __init__(self, name: str, unit: ProductUnit) -> None:
        self.name = name
        self.unit = unit


class ProductQuantity:
    """Uma linha adicionada ao carrinho: produto e quantidade (unidades ou quilos)."""

    def __init__(self, product: Product, quantity: float) -> None:
        self.product = product
        self.quantity = quantity


class ProductUnit(Enum):
    """Forma de venda: por unidade (EACH) ou por peso (KILO)."""

    EACH = 1
    KILO = 2


class SpecialOfferType(Enum):
    """Os quatro tipos de oferta do legado (RF01 a RF04)."""

    THREE_FOR_TWO = 1
    TEN_PERCENT_DISCOUNT = 2
    TWO_FOR_AMOUNT = 3
    FIVE_FOR_AMOUNT = 4


class Offer:
    """Oferta antiga cadastrada para um produto; argument depende do tipo."""

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
    """Linha de desconto do recibo; discount_amount é negativo quando reduz o total."""

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
