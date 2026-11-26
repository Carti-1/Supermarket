"""Fábrica de estratégias de oferta (Simple Factory / fábrica parametrizada).

Concentra num só lugar a decisão "para este tipo de oferta, qual estratégia
uso?". Assim o carrinho não precisa de if/elif por tipo (SRP: criar é
diferente de calcular) e depende apenas do contrato OfferStrategyPort (DIP).
Uma oferta nova é uma linha nova no registro, sem editar a lógica (OCP).
"""
from collections.abc import Callable, Mapping

from interfaces import OfferStrategyPort
from model_objects import SpecialOfferType
from offers.legacy_strategies import (
    FiveForAmountStrategy,
    PercentDiscountStrategy,
    ThreeForTwoStrategy,
    TwoForAmountStrategy,
)

StrategyRegistry = Mapping[SpecialOfferType, Callable[[], OfferStrategyPort]]

DEFAULT_REGISTRY: StrategyRegistry = {
    SpecialOfferType.THREE_FOR_TWO: ThreeForTwoStrategy,
    SpecialOfferType.TEN_PERCENT_DISCOUNT: PercentDiscountStrategy,
    SpecialOfferType.TWO_FOR_AMOUNT: TwoForAmountStrategy,
    SpecialOfferType.FIVE_FOR_AMOUNT: FiveForAmountStrategy,
}


class OfferStrategyFactory:
    """Escolhe a estratégia de cálculo para cada tipo de oferta."""

    def __init__(self, registry: StrategyRegistry | None = None) -> None:
        # Registro injetável: os testes passam estratégias falsas (stubs).
        # A cópia impede que mudanças no dicionário original afetem a fábrica.
        source = DEFAULT_REGISTRY if registry is None else registry
        self._registry = dict(source)

    def create(self, offer_type: SpecialOfferType) -> OfferStrategyPort:
        """Devolve uma nova estratégia para o tipo de oferta informado."""
        try:
            strategy_class = self._registry[offer_type]
        except KeyError:
            raise ValueError(
                f"Tipo de oferta sem estratégia registrada: {offer_type}"
            ) from None
        return strategy_class()