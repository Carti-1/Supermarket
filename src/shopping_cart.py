from collections.abc import Callable, Mapping

from interfaces import (
    CatalogReaderPort,
    OfferStrategyPort,
    ReceiptWriterPort,
    ShoppingCartPort,
)
from model_objects import Offer, Product, ProductQuantity, SpecialOfferType
from offers.offer_factory import OfferStrategyFactory

StrategyFactory = Callable[[SpecialOfferType], OfferStrategyPort]


class ShoppingCart(ShoppingCartPort):
    """Carrinho de compras: guarda os itens e delega o cálculo das ofertas."""

    def __init__(self, strategy_factory: StrategyFactory | None = None) -> None:
        # Injeção com valor padrão: ShoppingCart() continua funcionando como antes.
        self._strategy_factory = strategy_factory or OfferStrategyFactory().create
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
        """Aplica as ofertas antigas e devolve as quantidades que sobraram para combos."""
        available_quantities: dict[Product, float] = {}
        for product, quantity in self._product_quantities.items():
            reserved = 0.0
            offer = offers.get(product)
            if offer is not None:
                strategy = self._strategy_factory(offer.offer_type)
                result = strategy.apply(offer, quantity, catalog.unit_price(product))
                if result.discount is not None:
                    receipt.add_discount(result.discount)
                reserved = result.reserved_quantity
            available_quantities[product] = max(quantity - reserved, 0.0)
        return available_quantities