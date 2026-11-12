import math
from collections.abc import Mapping

from interfaces import CatalogReaderPort, ReceiptWriterPort, ShoppingCartPort
from model_objects import Discount, Offer, Product, ProductQuantity, SpecialOfferType


class ShoppingCart(ShoppingCartPort):

    def __init__(self) -> None:
        self._items: list[ProductQuantity] = []
        self._product_quantities: dict[Product, float] = {}

    @property
    def items(self) -> list[ProductQuantity]:
        return self._items

    def add_item(self, product: Product) -> None:
        self.add_item_quantity(product, 1.0)

    @property
    def product_quantities(self) -> dict[Product, float]:
        return self._product_quantities

    def add_item_quantity(self, product: Product, quantity: float) -> None:
        self._items.append(ProductQuantity(product, quantity))
        if product in self._product_quantities.keys():
            self._product_quantities[product] = self._product_quantities[product] + quantity
        else:
            self._product_quantities[product] = quantity

    def handle_offers(
        self,
        receipt: ReceiptWriterPort,
        offers: Mapping[Product, Offer],
        catalog: CatalogReaderPort,
    ) -> dict[Product, float]:
        """Aplica ofertas existentes e informa o saldo para combos posteriores.

        As fórmulas dos descontos permanecem iguais. O saldo reserva os grupos
        consumidos por ofertas antigas; quantidades excedentes continuam disponíveis.
        """
        available_quantities: dict[Product, float] = {}

        for p in self._product_quantities.keys():
            quantity = self._product_quantities[p]
            quantity_reserved = 0
            if p in offers.keys():
                offer = offers[p]
                unit_price = catalog.unit_price(p)
                quantity_as_int = int(quantity)
                discount = None
                x = 1
                if offer.offer_type == SpecialOfferType.THREE_FOR_TWO:
                    x = 3

                elif offer.offer_type == SpecialOfferType.TWO_FOR_AMOUNT:
                    x = 2
                    if quantity_as_int >= 2:
                        total = offer.argument * (quantity_as_int / x) + quantity_as_int % 2 * unit_price
                        discount_n = unit_price * quantity - total
                        discount = Discount(p, "2 for " + str(offer.argument), -discount_n)

                if offer.offer_type == SpecialOfferType.FIVE_FOR_AMOUNT:
                    x = 5

                number_of_x = math.floor(quantity_as_int / x)
                if offer.offer_type == SpecialOfferType.THREE_FOR_TWO and quantity_as_int > 2:
                    discount_amount = quantity * unit_price - (
                                (number_of_x * 2 * unit_price) + quantity_as_int % 3 * unit_price)
                    discount = Discount(p, "3 for 2", -discount_amount)
                    quantity_reserved = number_of_x * 3

                if offer.offer_type == SpecialOfferType.TWO_FOR_AMOUNT and quantity_as_int >= 2:
                    quantity_reserved = (quantity_as_int // 2) * 2

                if offer.offer_type == SpecialOfferType.TEN_PERCENT_DISCOUNT:
                    discount = Discount(p, str(offer.argument) + "% off",
                                        -quantity * unit_price * offer.argument / 100.0)
                    quantity_reserved = quantity

                if offer.offer_type == SpecialOfferType.FIVE_FOR_AMOUNT and quantity_as_int >= 5:
                    discount_total = unit_price * quantity - (
                                offer.argument * number_of_x + quantity_as_int % 5 * unit_price)
                    discount = Discount(p, str(x) + " for " + str(offer.argument), -discount_total)
                    quantity_reserved = number_of_x * 5

                if discount:
                    receipt.add_discount(discount)

            available_quantities[p] = max(quantity - quantity_reserved, 0.0)

        return available_quantities
