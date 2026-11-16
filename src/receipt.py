from __future__ import annotations

from itertools import chain

from interfaces import ReceiptReaderPort, ReceiptWriterPort
from model_objects import Discount, Product


class ReceiptItem:
    """Uma linha de produto no recibo: o que foi comprado e quanto custou."""

    def __init__(
        self,
        product: Product,
        quantity: float,
        price: float,
        total_price: float,
    ) -> None:
        self.product = product
        self.quantity = quantity
        self.price = price
        self.total_price = total_price


class Receipt(ReceiptReaderPort, ReceiptWriterPort):
    """Recibo de uma compra: guarda os itens e os descontos e calcula o total."""

    def __init__(self) -> None:
        self._items: list[ReceiptItem] = []
        self._discounts: list[Discount] = []

    def total_price(self) -> float | int:
        """Soma o valor dos itens e, depois, o dos descontos (que são negativos).

        Soma um valor por vez, na mesma ordem do código original. Trocar por
        sum() muda a ordem das somas e, em alguns recibos, o centavo impresso.
        """
        amounts = chain(
            (item.total_price for item in self._items),
            (discount.discount_amount for discount in self._discounts),
        )
        total = 0
        for amount in amounts:
            total += amount
        return total

    def add_product(
        self,
        product: Product,
        quantity: float,
        price: float,
        total_price: float,
    ) -> None:
        """Registra um produto comprado: quantidade, preço unitário e total da linha."""
        self._items.append(ReceiptItem(product, quantity, price, total_price))

    def add_discount(self, discount: Discount) -> None:
        """Registra um desconto já calculado (o valor dele é negativo)."""
        self._discounts.append(discount)

    @property
    def items(self) -> list[ReceiptItem]:
        """Itens do recibo. Devolve uma cópia, para quem chama não alterar o recibo."""
        return self._items[:]

    @property
    def discounts(self) -> list[Discount]:
        """Descontos do recibo. Devolve uma cópia, pelo mesmo motivo dos itens."""
        return self._discounts[:]
