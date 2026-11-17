# Este arquivo guarda o RECIBO da compra: as linhas de produtos, as linhas de
# desconto e o cálculo do total. Quem preenche o recibo é o Teller (caixa) e o
# ShoppingCart (carrinho); quem o lê e imprime é o ReceiptPrinter.

# Faz o Python tratar as anotações de tipo (como list[ReceiptItem] e float | int)
# como texto, sem avaliá-las na hora. Assim elas funcionam mesmo com classes
# definidas mais adiante no arquivo.
from __future__ import annotations

# chain junta várias sequências de valores em uma só, sem criar uma lista nova.
from itertools import chain

# Contratos definidos em interfaces.py:
# - ReceiptReaderPort: o que se pode LER de um recibo (items, discounts, total).
# - ReceiptWriterPort: o que se pode ESCREVER nele (add_product, add_discount).
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
        self.product = product          # qual produto foi comprado
        self.quantity = quantity        # quanto (float, porque pode ser em quilos)
        self.price = price              # preço de UMA unidade (ou de 1 kg)
        self.total_price = total_price  # valor da linha: quantidade x preço


class Receipt(ReceiptReaderPort, ReceiptWriterPort):
    """Recibo de uma compra: guarda os itens e os descontos e calcula o total."""

    def __init__(self) -> None:
        # O "_" no começo avisa: são de uso interno da classe. O resto do sistema
        # lê esses dados pelas propriedades items e discounts, mais abaixo.
        self._items: list[ReceiptItem] = []
        self._discounts: list[Discount] = []

    def total_price(self) -> float | int:
        """Soma o valor dos itens e, depois, o dos descontos (que são negativos).

        Soma um valor por vez, na mesma ordem do código original. Trocar por
        sum() muda a ordem das somas e, em alguns recibos, o centavo impresso.
        """
        # Primeiro todos os totais dos itens, depois todos os descontos, como
        # no original. Os descontos são números negativos, então somá-los
        # diminui o total.
        amounts = chain(
            (item.total_price for item in self._items),
            (discount.discount_amount for discount in self._discounts),
        )
        # Começa em 0 (inteiro) para que um recibo vazio devolva 0, igual ao
        # legado. Por isso o tipo de retorno é float | int.
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
        # Chamado pelo Teller, uma vez para cada item do carrinho.
        self._items.append(ReceiptItem(product, quantity, price, total_price))

    def add_discount(self, discount: Discount) -> None:
        """Registra um desconto já calculado (o valor dele é negativo)."""
        # Chamado pelo ShoppingCart (ofertas antigas) e, no futuro, pelo cálculo
        # de combos. O Receipt só guarda; quem calcula o desconto é outro módulo.
        self._discounts.append(discount)

    @property
    def items(self) -> list[ReceiptItem]:
        """Itens do recibo. Devolve uma cópia, para quem chama não alterar o recibo."""
        # [:] cria uma cópia da lista. Se devolvêssemos a própria lista, quem
        # chamasse poderia fazer recibo.items.clear() e apagar o recibo por fora.
        return self._items[:]

    @property
    def discounts(self) -> list[Discount]:
        """Descontos do recibo. Devolve uma cópia, pelo mesmo motivo dos itens."""
        return self._discounts[:]