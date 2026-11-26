"""Testes unitários das estratégias de oferta antigas.

Cada estratégia é testada sozinha, sem carrinho nem caixa. Os valores
esperados são os mesmos da caracterização (tests/test_comportamento_legado.py),
porque a extração das regras não pode mudar nenhum resultado.
"""
import pytest

from interfaces import OfferStrategyPort
from model_objects import Offer, Product, ProductUnit, SpecialOfferType
from offers.legacy_strategies import (
    FiveForAmountStrategy,
    PercentDiscountStrategy,
    ThreeForTwoStrategy,
    TwoForAmountStrategy,
)

PRODUTO = Product("produto", ProductUnit.EACH)
PRECO = 10.0


def _oferta(tipo, argumento=0.0):
    return Offer(tipo, PRODUTO, argumento)


def _confere(resultado, desconto, reservado):
    """desconto=None significa que a estratégia não gerou desconto."""
    if desconto is None:
        assert resultado.discount is None
    else:
        assert resultado.discount.discount_amount == pytest.approx(desconto)
        assert resultado.discount.product is PRODUTO
    assert resultado.reserved_quantity == pytest.approx(reservado)


@pytest.mark.parametrize("estrategia", [
    ThreeForTwoStrategy(),
    PercentDiscountStrategy(),
    TwoForAmountStrategy(),
    FiveForAmountStrategy(),
])
def test_toda_estrategia_cumpre_o_contrato(estrategia):
    assert isinstance(estrategia, OfferStrategyPort)


@pytest.mark.parametrize("quantidade, desconto, reservado", [
    (2, None, 0),
    (3, -10.0, 3),
    (4, -10.0, 3),
    (7, -20.0, 6),
])
def test_tres_por_dois(quantidade, desconto, reservado):
    oferta = _oferta(SpecialOfferType.THREE_FOR_TWO)
    resultado = ThreeForTwoStrategy().apply(oferta, quantidade, PRECO)
    _confere(resultado, desconto, reservado)


def test_tres_por_dois_descricao():
    oferta = _oferta(SpecialOfferType.THREE_FOR_TWO)
    assert ThreeForTwoStrategy().apply(oferta, 3, PRECO).discount.description == "3 for 2"


@pytest.mark.parametrize("quantidade, desconto", [(1, -1.0), (3, -3.0)])
def test_desconto_percentual_reserva_toda_a_quantidade(quantidade, desconto):
    oferta = _oferta(SpecialOfferType.TEN_PERCENT_DISCOUNT, 10.0)
    resultado = PercentDiscountStrategy().apply(oferta, quantidade, PRECO)
    _confere(resultado, desconto, quantidade)
    assert resultado.discount.description == "10.0% off"


@pytest.mark.parametrize("quantidade, desconto, reservado", [
    (1, None, 0),
    (2, -5.0, 2),
    (4, -10.0, 4),
    (3, 2.5, 2),    # defeito D3 do legado, mantido de propósito
])
def test_dois_por_valor(quantidade, desconto, reservado):
    oferta = _oferta(SpecialOfferType.TWO_FOR_AMOUNT, 15.0)
    resultado = TwoForAmountStrategy().apply(oferta, quantidade, PRECO)
    _confere(resultado, desconto, reservado)


@pytest.mark.parametrize("quantidade, desconto, reservado", [
    (4, None, 0),
    (5, -10.0, 5),
    (11, -20.0, 10),
])
def test_cinco_por_valor(quantidade, desconto, reservado):
    oferta = _oferta(SpecialOfferType.FIVE_FOR_AMOUNT, 40.0)
    resultado = FiveForAmountStrategy().apply(oferta, quantidade, PRECO)
    _confere(resultado, desconto, reservado)
