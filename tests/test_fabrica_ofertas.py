"""Testes da fábrica de estratégias de oferta.

A fábrica é testada com estratégias falsas (stubs) para não depender do
cálculo real das ofertas; só o registro padrão usa as classes verdadeiras.
"""
import pytest

from model_objects import SpecialOfferType
from offers.legacy_strategies import (
    FiveForAmountStrategy,
    PercentDiscountStrategy,
    ThreeForTwoStrategy,
    TwoForAmountStrategy,
)
from offers.offer_factory import DEFAULT_REGISTRY, OfferStrategyFactory


class EstrategiaFalsa:
    """Dublê que cumpre o contrato OfferStrategyPort sem calcular nada."""

    def apply(self, offer, quantity, unit_price):
        return None


def test_fabrica_cria_a_estrategia_registrada():
    fabrica = OfferStrategyFactory({SpecialOfferType.THREE_FOR_TWO: EstrategiaFalsa})

    assert isinstance(fabrica.create(SpecialOfferType.THREE_FOR_TWO), EstrategiaFalsa)


def test_fabrica_rejeita_tipo_sem_estrategia():
    with pytest.raises(ValueError, match="THREE_FOR_TWO"):
        OfferStrategyFactory({}).create(SpecialOfferType.THREE_FOR_TWO)


def test_fabrica_nao_e_afetada_por_mudancas_no_registro_recebido():
    registro = {SpecialOfferType.THREE_FOR_TWO: EstrategiaFalsa}
    fabrica = OfferStrategyFactory(registro)

    registro.clear()

    assert isinstance(fabrica.create(SpecialOfferType.THREE_FOR_TWO), EstrategiaFalsa)


def test_registro_padrao_cobre_todos_os_tipos_legados():
    assert set(DEFAULT_REGISTRY) == set(SpecialOfferType)


@pytest.mark.parametrize(
    "tipo, classe_esperada",
    [
        (SpecialOfferType.THREE_FOR_TWO, ThreeForTwoStrategy),
        (SpecialOfferType.TEN_PERCENT_DISCOUNT, PercentDiscountStrategy),
        (SpecialOfferType.TWO_FOR_AMOUNT, TwoForAmountStrategy),
        (SpecialOfferType.FIVE_FOR_AMOUNT, FiveForAmountStrategy),
    ],
)
def test_registro_padrao_associa_cada_tipo_a_sua_estrategia(tipo, classe_esperada):
    assert type(OfferStrategyFactory().create(tipo)) is classe_esperada