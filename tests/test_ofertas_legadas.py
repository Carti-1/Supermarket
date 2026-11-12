import pytest

from model_objects import Product, ProductUnit, SpecialOfferType
from receipt import Receipt
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


@pytest.mark.parametrize(
    (
        "tipo_oferta",
        "quantidade",
        "argumento",
        "total_esperado",
        "desconto_esperado",
        "quantidade_disponivel_esperada",
    ),
    [
        (None, 2.0, 0.0, 20.0, None, 2.0),
        (SpecialOfferType.THREE_FOR_TWO, 2.0, 0.0, 20.0, None, 2.0),
        (SpecialOfferType.THREE_FOR_TWO, 3.0, 0.0, 20.0, -10.0, 0.0),
        (SpecialOfferType.THREE_FOR_TWO, 4.0, 0.0, 30.0, -10.0, 1.0),
        (SpecialOfferType.TWO_FOR_AMOUNT, 1.0, 15.0, 10.0, None, 1.0),
        (SpecialOfferType.TWO_FOR_AMOUNT, 2.0, 15.0, 15.0, -5.0, 0.0),
        (SpecialOfferType.FIVE_FOR_AMOUNT, 4.0, 40.0, 40.0, None, 4.0),
        (SpecialOfferType.FIVE_FOR_AMOUNT, 5.0, 40.0, 40.0, -10.0, 0.0),
        (SpecialOfferType.FIVE_FOR_AMOUNT, 6.0, 40.0, 50.0, -10.0, 1.0),
        (SpecialOfferType.TEN_PERCENT_DISCOUNT, 2.0, 10.0, 18.0, -2.0, 0.0),
    ],
)
def test_ofertas_legadas_mantem_o_resultado_esperado(
    tipo_oferta,
    quantidade,
    argumento,
    total_esperado,
    desconto_esperado,
    quantidade_disponivel_esperada,
):
    produto = Product("produto de teste", ProductUnit.EACH)
    catalogo = FakeCatalog()
    catalogo.add_product(produto, 10.0)
    caixa = Teller(catalogo)
    carrinho = ShoppingCart()
    carrinho.add_item_quantity(produto, quantidade)

    if tipo_oferta is not None:
        caixa.add_special_offer(tipo_oferta, produto, argumento)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(total_esperado)
    if desconto_esperado is None:
        assert recibo.discounts == []
    else:
        assert len(recibo.discounts) == 1
        assert recibo.discounts[0].discount_amount == pytest.approx(
            desconto_esperado
        )

    # Confirma o saldo que o futuro calculador de combos poderá consumir sem
    # reaproveitar quantidades já contempladas por uma oferta antiga.
    quantidades_disponiveis = carrinho.handle_offers(
        Receipt(), caixa.offers, catalogo
    )
    assert quantidades_disponiveis[produto] == pytest.approx(
        quantidade_disponivel_esperada
    )
