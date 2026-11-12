import pytest

from model_objects import Combo, Discount, Product, ProductUnit, SpecialOfferType
from shopping_cart import ShoppingCart
from teller import Teller
from tests.fake_catalog import FakeCatalog


def _preparar_checkout():
    """Prepara o exemplo do enunciado: escova a R$ 10,00 e creme a R$ 15,00."""
    escova = Product("escova", ProductUnit.EACH)
    creme_dental = Product("creme dental", ProductUnit.EACH)
    catalogo = FakeCatalog()
    catalogo.add_product(escova, 10.0)
    catalogo.add_product(creme_dental, 15.0)
    caixa = Teller(catalogo)
    carrinho = ShoppingCart()
    combo = Combo("Higiene bucal", {escova: 1.0, creme_dental: 1.0})
    caixa.add_combo_offer(combo)
    return escova, creme_dental, caixa, carrinho


def test_combo_define_composicao_e_percentual_exigidos():
    """Registra a composição fixa e o percentual estabelecido no enunciado."""
    escova = Product("escova", ProductUnit.EACH)
    creme_dental = Product("creme dental", ProductUnit.EACH)

    combo = Combo("Higiene bucal", {escova: 1.0, creme_dental: 1.0})

    assert combo.name == "Higiene bucal"
    assert combo.required_quantities == {escova: 1.0, creme_dental: 1.0}
    assert combo.discount_percentage == 10.0


@pytest.mark.parametrize(
    "nome,composicao",
    [
        ("", {Product("escova", ProductUnit.EACH): 1.0}),
        ("Higiene bucal", {}),
        ("Higiene bucal", {Product("escova", ProductUnit.EACH): 0.0}),
        ("Higiene bucal", {Product("escova", ProductUnit.EACH): -1.0}),
    ],
)
def test_combo_rejeita_definicoes_sem_composicao_valida(nome, composicao):
    """Impede combos sem nome, sem produtos ou com quantidades impossíveis."""
    with pytest.raises(ValueError):
        Combo(nome, composicao)


@pytest.mark.xfail(
    strict=True,
    reason="O cálculo promocional de combos será implementado na próxima etapa.",
)
def test_combo_completo_aplica_dez_por_cento_somente_aos_itens_do_combo():
    """Exige 10% de desconto em R$ 25,00 quando os dois produtos estão presentes."""
    escova, creme_dental, caixa, carrinho = _preparar_checkout()
    carrinho.add_item_quantity(escova, 1.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(22.5)
    assert len(recibo.discounts) == 1
    assert recibo.discounts[0].discount_amount == pytest.approx(-2.5)


def test_combo_incompleto_nao_concede_desconto():
    """Mantém o preço normal quando falta um dos produtos exigidos pelo combo."""
    escova, _, caixa, carrinho = _preparar_checkout()
    carrinho.add_item_quantity(escova, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(10.0)
    assert recibo.discounts == []


def test_caixa_entrega_ao_calculador_somente_quantidades_restantes():
    """Mantém ofertas antigas primeiro e passa seu saldo ao módulo de combos."""
    escova, creme_dental, caixa, carrinho = _preparar_checkout()
    caixa.add_special_offer(SpecialOfferType.THREE_FOR_TWO, escova, 0.0)
    carrinho.add_item_quantity(escova, 4.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    class CalculadorDeTeste:
        """Dublê que registra o contrato sem implementar a regra de negócio."""

        quantidades_recebidas = None

        def calculate_discounts(self, combos, available_quantities, catalog):
            # Guardamos cópia para o teste verificar o dado recebido pelo caixa.
            self.quantidades_recebidas = dict(available_quantities)
            return [Discount(escova, "Desconto de combo simulado", -1.0)]

    calculador = CalculadorDeTeste()
    caixa.combo_promotion = calculador

    recibo = caixa.checks_out_articles_from(carrinho)

    assert calculador.quantidades_recebidas == {escova: 1.0, creme_dental: 1.0}
    assert sorted(desconto.discount_amount for desconto in recibo.discounts) == [
        -10.0,
        -1.0,
    ]
    assert recibo.total_price() == pytest.approx(44.0)


@pytest.mark.xfail(
    strict=True,
    reason="O cálculo promocional de combos será implementado na próxima etapa.",
)
def test_dois_conjuntos_completos_recebem_dois_descontos():
    """Exige um desconto por cada repetição completa da mesma composição."""
    escova, creme_dental, caixa, carrinho = _preparar_checkout()
    carrinho.add_item_quantity(escova, 2.0)
    carrinho.add_item_quantity(creme_dental, 2.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(45.0)
    assert len(recibo.discounts) == 2
    assert [desconto.discount_amount for desconto in recibo.discounts] == pytest.approx(
        [-2.5, -2.5]
    )


@pytest.mark.xfail(
    strict=True,
    reason="O cálculo promocional de combos será implementado na próxima etapa.",
)
def test_produto_excedente_fica_fora_do_desconto_do_combo():
    """Desconta um combo e mantém a segunda escova pelo preço normal."""
    escova, creme_dental, caixa, carrinho = _preparar_checkout()
    carrinho.add_item_quantity(escova, 2.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(32.5)
    assert len(recibo.discounts) == 1
    assert recibo.discounts[0].discount_amount == pytest.approx(-2.5)


@pytest.mark.xfail(
    strict=True,
    reason="A alocação entre ofertas antigas e combos será implementada na próxima etapa.",
)
def test_oferta_antiga_tem_prioridade_e_combo_usa_somente_excedentes():
    """Evita reutilizar no combo as três escovas alocadas à oferta 3 por 2."""
    escova, creme_dental, caixa, carrinho = _preparar_checkout()
    caixa.add_special_offer(SpecialOfferType.THREE_FOR_TWO, escova, 0.0)
    carrinho.add_item_quantity(escova, 4.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(42.5)
    assert sorted(desconto.discount_amount for desconto in recibo.discounts) == pytest.approx(
        [-10.0, -2.5]
    )
