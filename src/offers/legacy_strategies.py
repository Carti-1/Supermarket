"""Estratégia das ofertas antigas: uma classe por regra de negócio."""
from interfaces import OfferResult
from model_objects import Discount

NO_DISCOUNT = OfferResult(None, 0.0)


class ThreeForTwoStrategy:
    """Leve 3, pague 2: a cada grupo de 3 unidades, um sai de graça."""

    def apply(self, offer, quantity, unit_price):
        whole_units = int(quantity)
        if whole_units <= 2:
            return NO_DISCOUNT
        groups = whole_units // 3
        charge = groups * 2 * unit_price + whole_units % 3 * unit_price
        amount = quantity * unit_price - charge
        return OfferResult(Discount(offer.product, "3 por 2", -amount), groups * 3)

class PercentDiscountStrategy:
    """Desconto percentual sobre toda a quantidade do produto."""

    def apply(self, offer, quantity, unit_price):
        amount = quantity * unit_price * offer.argument / 100.0
        description = str(offer.argument) + "% off"
        return OfferResult(Discount(offer.product, description, -amount), quantity)


class TwoForAmountStrategy:
    """Dois por um valor fixo. Mantém a divisão real (/) do legado: defeito D3."""

    def apply(self, offer, quantity, unit_price):
        whole_units = int(quantity)
        if whole_units < 2:
            return NO_DISCOUNT
        charged = offer.argument * (whole_units / 2) + whole_units % 2 * unit_price
        amount = unit_price * quantity - charged
        description = "2 for " + str(offer.argument)
        return OfferResult(Discount(offer.product, description, -amount), (whole_units // 2) * 2)


class FiveForAmountStrategy:
    """Cinco por um valor fixo."""

    def apply(self, offer, quantity, unit_price):
        whole_units = int(quantity)
        if whole_units < 5:
            return NO_DISCOUNT
        groups = whole_units // 5
        charged = offer.argument * groups + whole_units % 5 * unit_price
        amount = unit_price * quantity - charged
        description = "5 for " + str(offer.argument)
        return OfferResult(Discount(offer.product, description, -amount), groups * 5)
