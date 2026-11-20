"""Testes de caracterização do comportamento LEGADO do Supermarket Receipt.

Cada teste registra o que o sistema faz HOJE, não o que deveria fazer.
Os valores esperados foram obtidos rodando o código original (branch main),
nunca calculados de cabeça.

Regra de ouro: só se testa o comportamento público que já existia no
original (Receipt.total_price, Receipt.discounts, Receipt.items). O retorno
de ShoppingCart.handle_offers NÃO é testado, porque no original ele é None
e o retorno novo é do contrato da equipe. Assim este mesmo arquivo roda
"antes" e "depois" da refatoração.
"""
import pytest

from model_objects import Product, ProductUnit, SpecialOfferType
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


def _checkout(preco, quantidade, oferta=None, argumento=0.0, unidade=ProductUnit.EACH):
    """Monta catálogo, caixa e carrinho com um produto e devolve o recibo."""
    produto = Product("produto", unidade)
    catalogo = FakeCatalog()
    catalogo.add_product(produto, preco)
    caixa = Teller(catalogo)
    if oferta is not None:
        caixa.add_special_offer(oferta, produto, argumento)
    carrinho = ShoppingCart()
    carrinho.add_item_quantity(produto, quantidade)
    return caixa.checks_out_articles_from(carrinho)


def _confere(recibo, total, desconto):
    """desconto=None significa que o recibo não tem nenhuma linha de desconto."""
    assert recibo.total_price() == pytest.approx(total)
    if desconto is None:
        assert recibo.discounts == []
    else:
        assert len(recibo.discounts) == 1
        assert recibo.discounts[0].discount_amount == pytest.approx(desconto)


# ---------- Sem oferta ----------

def test_sem_oferta_nao_gera_desconto():
    _confere(_checkout(10.0, 3), 30.0, None)


def test_sem_oferta_produto_por_quilo():
    _confere(_checkout(3.0, 0.5, unidade=ProductUnit.KILO), 1.5, None)


# ---------- 3 por 2 ----------

@pytest.mark.parametrize("quantidade, total, desconto", [
    (1, 10.0, None),   # abaixo do mínimo: sem desconto
    (2, 20.0, None),
    (3, 20.0, -10.0),  # um grupo completo
    (4, 30.0, -10.0),  # um grupo + 1 avulsa
    (6, 40.0, -20.0),  # dois grupos
    (7, 50.0, -20.0),  # dois grupos + 1 avulsa
])
def test_tres_por_dois_com_varios_grupos(quantidade, total, desconto):
    recibo = _checkout(10.0, quantidade, SpecialOfferType.THREE_FOR_TWO)
    _confere(recibo, total, desconto)


# ---------- 2 por X ----------

@pytest.mark.parametrize("quantidade, total, desconto", [
    (1, 10.0, None),
    (2, 15.0, -5.0),
    (4, 30.0, -10.0),
    (6, 45.0, -15.0),
])
def test_dois_por_valor_com_quantidade_par(quantidade, total, desconto):
    recibo = _checkout(10.0, quantidade, SpecialOfferType.TWO_FOR_AMOUNT, 15.0)
    _confere(recibo, total, desconto)


@pytest.mark.parametrize("quantidade, total, desconto", [
    (3, 32.5, 2.5),    # cobra MAIS que os 30,00 sem oferta; o "desconto" é positivo
    (5, 47.5, -2.5),   # o correto seria 40,00
    (7, 62.5, -7.5),   # o correto seria 55,00
])
def test_dois_por_valor_com_quantidade_impar_registra_defeito_do_legado(quantidade, total, desconto):
    """CARACTERIZAÇÃO DE DEFEITO (D3): com quantidade ímpar >= 3 o legado calcula
    errado, porque usa divisão com vírgula (quantity / 2) em vez de divisão inteira.

    Os valores acima são mantidos DE PROPÓSITO, pois descrevem o original.
    Qualquer correção deve vir em um commit fix: separado, decidido em grupo,
    e estes valores passam a ser atualizados junto com ele.
    """
    recibo = _checkout(10.0, quantidade, SpecialOfferType.TWO_FOR_AMOUNT, 15.0)
    _confere(recibo, total, desconto)


# ---------- 5 por X ----------

@pytest.mark.parametrize("quantidade, total, desconto", [
    (4, 40.0, None),   # abaixo do mínimo
    (5, 40.0, -10.0),
    (6, 50.0, -10.0),
    (10, 80.0, -20.0),
    (11, 90.0, -20.0),
])
def test_cinco_por_valor_com_varios_grupos(quantidade, total, desconto):
    recibo = _checkout(10.0, quantidade, SpecialOfferType.FIVE_FOR_AMOUNT, 40.0)
    _confere(recibo, total, desconto)


# ---------- 10% de desconto ----------

@pytest.mark.parametrize("quantidade, total, desconto", [
    (1, 9.0, -1.0),
    (3, 27.0, -3.0),
])
def test_dez_por_cento_de_desconto(quantidade, total, desconto):
    recibo = _checkout(10.0, quantidade, SpecialOfferType.TEN_PERCENT_DISCOUNT, 10.0)
    _confere(recibo, total, desconto)


# ---------- Produto por quilo (quantidade fracionária) ----------

def test_dez_por_cento_em_produto_por_quilo():
    recibo = _checkout(4.0, 2.5, SpecialOfferType.TEN_PERCENT_DISCOUNT, 10.0, ProductUnit.KILO)
    _confere(recibo, 9.0, -1.0)


def test_tres_por_dois_com_quilo_o_int_leva_a_fracao_junto():
    # O legado usa int(quantidade) para achar os grupos, mas o desconto usa a
    # quantidade real: os 0,5 kg que sobram saem de graça (35,00 - 15,00 = 20,00).
    recibo = _checkout(10.0, 3.5, SpecialOfferType.THREE_FOR_TWO, 0.0, ProductUnit.KILO)
    _confere(recibo, 20.0, -15.0)


def test_tres_por_dois_com_quilo_abaixo_de_tres_nao_tem_desconto():
    # int(2.9) == 2, então a oferta não entra.
    recibo = _checkout(10.0, 2.9, SpecialOfferType.THREE_FOR_TWO, 0.0, ProductUnit.KILO)
    _confere(recibo, 29.0, None)


# ---------- Carrinho e recibo ----------

def test_mesmo_produto_adicionado_duas_vezes_gera_duas_linhas_mas_oferta_usa_a_soma():
    escova = Product("escova", ProductUnit.EACH)
    catalogo = FakeCatalog()
    catalogo.add_product(escova, 10.0)
    caixa = Teller(catalogo)
    caixa.add_special_offer(SpecialOfferType.THREE_FOR_TWO, escova, 0.0)
    carrinho = ShoppingCart()
    carrinho.add_item(escova)
    carrinho.add_item_quantity(escova, 2.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert [item.quantity for item in recibo.items] == [1.0, 2.0]
    assert len(recibo.discounts) == 1
    assert recibo.discounts[0].discount_amount == pytest.approx(-10.0)
    assert recibo.total_price() == pytest.approx(20.0)


def test_varios_produtos_com_ofertas_diferentes_no_mesmo_carrinho():
    escova = Product("escova", ProductUnit.EACH)
    pasta = Product("pasta", ProductUnit.EACH)
    arroz = Product("arroz", ProductUnit.EACH)
    sabao = Product("sabao", ProductUnit.EACH)
    catalogo = FakeCatalog()
    catalogo.add_product(escova, 0.99)
    catalogo.add_product(pasta, 1.79)
    catalogo.add_product(arroz, 2.49)
    catalogo.add_product(sabao, 5.0)
    caixa = Teller(catalogo)
    caixa.add_special_offer(SpecialOfferType.THREE_FOR_TWO, escova, 0.0)
    caixa.add_special_offer(SpecialOfferType.TEN_PERCENT_DISCOUNT, pasta, 20.0)
    caixa.add_special_offer(SpecialOfferType.TWO_FOR_AMOUNT, arroz, 4.0)
    carrinho = ShoppingCart()
    carrinho.add_item_quantity(escova, 3.0)
    carrinho.add_item_quantity(pasta, 2.0)
    carrinho.add_item_quantity(arroz, 4.0)
    carrinho.add_item_quantity(sabao, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    # sabão não tem oferta: nenhuma linha de desconto para ele
    descontos = [(d.product.name, d.description, d.discount_amount) for d in recibo.discounts]
    assert [(nome, descricao) for nome, descricao, _ in descontos] == [
        ("escova", "3 for 2"),
        ("pasta", "20.0% off"),
        ("arroz", "2 for 4.0"),
    ]
    assert [valor for _, _, valor in descontos] == pytest.approx([-0.99, -0.716, -1.96])
    assert recibo.total_price() == pytest.approx(17.844)


def test_carrinho_vazio_tem_total_zero_e_nenhuma_linha():
    caixa = Teller(FakeCatalog())

    recibo = caixa.checks_out_articles_from(ShoppingCart())

    assert recibo.total_price() == 0
    assert recibo.items == []
    assert recibo.discounts == []


def test_oferta_para_produto_fora_do_carrinho_nao_gera_desconto():
    escova = Product("escova", ProductUnit.EACH)
    pasta = Product("pasta", ProductUnit.EACH)
    catalogo = FakeCatalog()
    catalogo.add_product(escova, 1.0)
    catalogo.add_product(pasta, 2.0)
    caixa = Teller(catalogo)
    caixa.add_special_offer(SpecialOfferType.THREE_FOR_TWO, escova, 0.0)
    carrinho = ShoppingCart()
    carrinho.add_item_quantity(pasta, 3.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.discounts == []
    assert recibo.total_price() == pytest.approx(6.0)


@pytest.mark.parametrize("oferta, argumento, quantidade, descricao", [
    (SpecialOfferType.THREE_FOR_TWO, 0.0, 3, "3 for 2"),
    (SpecialOfferType.TEN_PERCENT_DISCOUNT, 10.0, 1, "10.0% off"),
    (SpecialOfferType.TWO_FOR_AMOUNT, 15.0, 2, "2 for 15.0"),
    (SpecialOfferType.FIVE_FOR_AMOUNT, 40.0, 5, "5 for 40.0"),
])
def test_descricao_e_produto_de_cada_desconto(oferta, argumento, quantidade, descricao):
    recibo = _checkout(10.0, quantidade, oferta, argumento)

    assert len(recibo.discounts) == 1
    assert recibo.discounts[0].description == descricao
    assert recibo.discounts[0].product.name == "produto"


def test_campos_do_item_do_recibo():
    recibo = _checkout(0.99, 2.0)

    assert len(recibo.items) == 1
    item = recibo.items[0]
    assert item.product.name == "produto"
    assert item.quantity == 2.0
    assert item.price == pytest.approx(0.99)
    assert item.total_price == pytest.approx(1.98)
