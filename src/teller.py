from interfaces import (
    CatalogReaderPort,
    ComboPromotionPort,
    ReceiptReaderPort,
    ShoppingCartPort,
)
from model_objects import Combo, Offer, Product, SpecialOfferType
from offers.combo_promotion import ComboPromotion
from receipt import Receipt


class Teller:

    def __init__(
        self,
        catalog: CatalogReaderPort,
        combo_promotion: ComboPromotionPort | None = None,
    ) -> None:
        """Monta o caixa com dependências substituíveis para facilitar testes.

        Sem injeção, o caixa usa o ComboPromotion real, então Teller(catalog)
        já aplica combos. Os testes ainda podem passar um dublê (DIP).
        """
        self.catalog = catalog
        self.combo_promotion = (
            combo_promotion if combo_promotion is not None else ComboPromotion()
        )
        self.offers: dict[Product, Offer] = {}
        self.combo_offers: list[Combo] = []

    def add_special_offer(
        self,
        offer_type: SpecialOfferType,
        product: Product,
        argument: float,
    ) -> None:
        self.offers[product] = Offer(offer_type, product, argument)

    def add_combo_offer(self, combo: Combo) -> None:
        """Registra a composição promocional que será aplicada no checkout."""
        self.combo_offers.append(combo)

    def checks_out_articles_from(
        self,
        the_cart: ShoppingCartPort,
    ) -> ReceiptReaderPort:
        """Fecha a compra na ordem definida para evitar desconto duplicado.

        Primeiro registra produtos e aplica as ofertas legadas. Só então envia ao
        calculador de combos as quantidades que essas ofertas deixaram disponíveis.
        """
        receipt = Receipt()
        for item in the_cart.items:
            product = item.product
            quantity = item.quantity
            unit_price = self.catalog.unit_price(product)
            price = quantity * unit_price
            receipt.add_product(product, quantity, unit_price, price)

        available_quantities = the_cart.handle_offers(
            receipt,
            self.offers,
            self.catalog,
        )

        if self.combo_offers:
            combo_discounts = self.combo_promotion.calculate_discounts(
                self.combo_offers,
                available_quantities,
                self.catalog,
            )
            for discount in combo_discounts:
                receipt.add_discount(discount)

        return receipt

    def product_with_name(self, name: str) -> Product | None:
        return self.catalog.product_by_name(name)