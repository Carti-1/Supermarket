from collections.abc import Mapping

from catalog import SupermarketCatalog
from interfaces import (
    CatalogReaderPort,
    CatalogWriterPort,
    ReceiptItemPort,
    ReceiptReaderPort,
    ReceiptWriterPort,
    ShoppingCartPort,
)
from model_objects import Discount, Offer, Product, ProductQuantity, ProductUnit
from receipt import Receipt
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


def test_fake_catalog_implementa_as_portas_de_leitura_e_escrita():
    catalogo: SupermarketCatalog = FakeCatalog()
    produto = Product("leite", ProductUnit.EACH)

    catalogo.add_product(produto, 4.5)

    assert isinstance(catalogo, CatalogReaderPort)
    assert isinstance(catalogo, CatalogWriterPort)
    assert catalogo.unit_price(produto) == 4.5
    assert catalogo.product_by_name("leite") is produto
    assert catalogo.product_by_name("produto inexistente") is None


def test_recibo_implementa_as_portas_de_escrita_e_leitura():
    produto = Product("arroz", ProductUnit.EACH)
    desconto = Discount(produto, "Desconto de teste", -1.0)
    recibo = Receipt()

    recibo.add_product(produto, 2.0, 3.0, 6.0)
    recibo.add_discount(desconto)

    assert isinstance(recibo, ReceiptWriterPort)
    assert isinstance(recibo, ReceiptReaderPort)
    assert isinstance(recibo.items[0], ReceiptItemPort)
    assert recibo.items[0].product is produto
    assert recibo.discounts == [desconto]
    assert recibo.total_price() == 5.0


def test_carrinho_real_implementa_o_contrato_consumido_pelo_caixa():
    assert isinstance(ShoppingCart(), ShoppingCartPort)


def test_caixa_usa_as_interfaces_de_catalogo_carrinho_e_recibo():
    produto = Product("cafe", ProductUnit.EACH)
    catalogo = FakeCatalog()
    catalogo.add_product(produto, 2.0)
    carrinho = ShoppingCart()
    carrinho.add_item_quantity(produto, 2.0)
    caixa = Teller(catalogo)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert isinstance(recibo, ReceiptReaderPort)
    assert caixa.product_with_name("cafe") is produto
    assert caixa.product_with_name("produto inexistente") is None
    assert recibo.total_price() == 4.0
    assert recibo.items[0].quantity == 2.0


def test_caixa_aceita_carrinho_estrutural_compativel_com_o_contrato():
    produto = Product("cha", ProductUnit.EACH)
    catalogo = FakeCatalog()
    catalogo.add_product(produto, 2.0)

    class CarrinhoDeTeste:
        @property
        def items(self) -> list[ProductQuantity]:
            return [ProductQuantity(produto, 2.0)]

        def handle_offers(
            self,
            recibo: ReceiptWriterPort,
            ofertas: Mapping[Product, Offer],
            catalogo_recebido: CatalogReaderPort,
        ) -> Mapping[Product, float]:
            recibo.add_discount(Discount(produto, "Desconto de teste", -0.5))
            # O contrato informa ao caixa quanto sobrou para uma promoção posterior.
            return {produto: 2.0}

    carrinho = CarrinhoDeTeste()
    caixa = Teller(catalogo)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert isinstance(carrinho, ShoppingCartPort)
    assert recibo.total_price() == 3.5
    assert recibo.discounts[0].discount_amount == -0.5
