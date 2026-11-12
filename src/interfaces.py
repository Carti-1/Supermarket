"""Contratos compartilhados entre os módulos do comprovante de supermercado."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

from model_objects import Combo, Discount, Offer, Product, ProductQuantity


@runtime_checkable
class ReceiptItemPort(Protocol):
    """Campos de leitura compartilhados pelas linhas do comprovante."""

    product: Product
    quantity: float
    price: float
    total_price: float


@runtime_checkable
class CatalogReaderPort(Protocol):
    """Operações de consulta usadas pelo caixa e pelo cálculo de ofertas."""

    def unit_price(self, product: Product) -> float:
        """Retorna o preço unitário do produto."""
        ...

    def product_by_name(self, name: str) -> Product | None:
        """Retorna o produto pelo nome ou None se ele não estiver no catálogo."""
        ...


@runtime_checkable
class CatalogWriterPort(Protocol):
    """Operação usada para cadastrar produtos no catálogo."""

    def add_product(self, product: Product, price: float) -> None:
        """Cadastra um produto e seu preço unitário no catálogo."""
        ...


@runtime_checkable
class ReceiptWriterPort(Protocol):
    """Operações para adicionar os resultados do checkout ao comprovante."""

    def add_product(
        self,
        product: Product,
        quantity: float,
        price: float,
        total_price: float,
    ) -> None:
        """Adiciona ao comprovante uma linha de produto com seu preço."""
        ...

    def add_discount(self, discount: Discount) -> None:
        """Adiciona uma linha de desconto ao comprovante."""
        ...


@runtime_checkable
class ReceiptReaderPort(Protocol):
    """Informações somente para leitura retornadas pelo checkout."""

    @property
    def items(self) -> Sequence[ReceiptItemPort]:
        """Linhas de produtos do comprovante."""
        ...

    @property
    def discounts(self) -> Sequence[Discount]:
        """Linhas de descontos do comprovante."""
        ...

    def total_price(self) -> float | int:
        """Retorna o total do comprovante, incluindo os descontos."""
        ...


@runtime_checkable
class ShoppingCartPort(Protocol):
    """Operações do carrinho usadas pelo caixa."""

    @property
    def items(self) -> Sequence[ProductQuantity]:
        """Itens do carrinho que devem entrar no checkout."""
        ...

    def handle_offers(
        self,
        receipt: ReceiptWriterPort,
        offers: Mapping[Product, Offer],
        catalog: CatalogReaderPort,
    ) -> Mapping[Product, float]:
        """Aplica ofertas antigas e retorna quantidades ainda disponíveis.

        O retorno permite que o calculador de combos use somente produtos que não
        participaram de outra promoção, evitando aplicar dois descontos à mesma
        quantidade.
        """
        ...


class ComboPromotionPort(Protocol):
    """Calcula combos sem misturar essa regra às ofertas antigas.

    O caixa fornecerá apenas as quantidades restantes após aplicar as ofertas antigas.
    Assim, uma mesma quantidade não recebe dois descontos. A sequência recebida define
    a prioridade entre composições sobrepostas.
    """

    def calculate_discounts(
        self,
        combos: Sequence[Combo],
        available_quantities: Mapping[Product, float],
        catalog: CatalogReaderPort,
    ) -> Sequence[Discount]:
        """Calcula descontos apenas com quantidades não usadas por outras ofertas.

        Cada combo completo gera 10% de desconto sobre os produtos e as quantidades
        que o compõem. A sequência define a prioridade entre combos diferentes;
        quantidades excedentes permanecem disponíveis e não recebem desconto por si.
        """
        ...
