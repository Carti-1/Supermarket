import pytest

from model_objects import Combo, Discount, Product, ProductUnit, SpecialOfferType
from offers.combo_promotion import ComboPromotion
from receipt_printer import ReceiptPrinter
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


def test_produto_excedente_fica_fora_do_desconto_do_combo():
    """Desconta um combo e mantém a segunda escova pelo preço normal."""
    escova, creme_dental, caixa, carrinho = _preparar_checkout()
    carrinho.add_item_quantity(escova, 2.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(32.5)
    assert len(recibo.discounts) == 1
    assert recibo.discounts[0].discount_amount == pytest.approx(-2.5)


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


# ---------------------------------------------------------------------------
# Cenários pelo caixa com o ComboPromotion injetado (Lucca).
# Os testes acima usam Teller(catalogo) sem injeção: desde que o Teller passou a
# usar o ComboPromotion por padrão, eles cobrem o mesmo cálculo pelo caminho normal.
# Valores calculados à mão: escova R$ 10,00, creme R$ 15,00, fio R$ 5,00.
# ---------------------------------------------------------------------------

def _caixa_com_combo():
    """Mesmo cenário do enunciado, mas com o cálculo real de combos injetado."""
    escova, creme_dental, caixa, carrinho = _preparar_checkout()
    caixa.combo_promotion = ComboPromotion()
    return escova, creme_dental, caixa, carrinho


@pytest.mark.parametrize(
    "escovas,cremes,total,descontos",
    [
        (1.0, 1.0, 22.5, [-2.5]),          # RF07 combo completo
        (1.0, 0.0, 10.0, []),              # RF08 combo incompleto
        (2.0, 2.0, 45.0, [-2.5, -2.5]),    # RF09 duas repetições
        (2.0, 1.0, 32.5, [-2.5]),          # RF10 escova excedente com preço normal
    ],
)
def test_cenarios_do_enunciado_com_combo_injetado(escovas, cremes, total, descontos):
    escova, creme_dental, caixa, carrinho = _caixa_com_combo()
    carrinho.add_item_quantity(escova, escovas)
    if cremes:
        carrinho.add_item_quantity(creme_dental, cremes)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(total)
    assert [d.discount_amount for d in recibo.discounts] == pytest.approx(descontos)


def test_tres_por_dois_tem_prioridade_e_combo_usa_a_sobra():
    """RF11/D1: 3 escovas ficam no 3 por 2 (−10,00); a 4ª forma combo (−2,50)."""
    escova, creme_dental, caixa, carrinho = _caixa_com_combo()
    caixa.add_special_offer(SpecialOfferType.THREE_FOR_TWO, escova, 0.0)
    carrinho.add_item_quantity(escova, 4.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(42.5)
    assert [d.discount_amount for d in recibo.discounts] == pytest.approx([-10.0, -2.5])


def test_dez_por_cento_individual_reserva_toda_a_quantidade():
    """RF11/D1: o 10% legado cobre a escova inteira, então não sobra para combo."""
    escova, creme_dental, caixa, carrinho = _caixa_com_combo()
    caixa.add_special_offer(SpecialOfferType.TEN_PERCENT_DISCOUNT, escova, 10.0)
    carrinho.add_item_quantity(escova, 1.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert recibo.total_price() == pytest.approx(24.0)
    assert [d.discount_amount for d in recibo.discounts] == pytest.approx([-1.0])


def test_dois_por_valor_reserva_duas_escovas_e_a_terceira_entra_no_combo():
    """RF11/D1: "2 for 15" reserva 2 escovas; sobra 1 → 1 combo de −2,50.

    O +2,50 da oferta antiga é o defeito D3 do legado (3 unidades no "2 for 15"
    cobram R$ 32,50). Ele foi mantido de propósito; o combo não o corrige nem
    o duplica.
    """
    escova, creme_dental, caixa, carrinho = _caixa_com_combo()
    caixa.add_special_offer(SpecialOfferType.TWO_FOR_AMOUNT, escova, 15.0)
    carrinho.add_item_quantity(escova, 3.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert [d.discount_amount for d in recibo.discounts] == pytest.approx([2.5, -2.5])
    assert recibo.total_price() == pytest.approx(45.0)


def test_combos_que_disputam_a_mesma_escova_seguem_a_ordem_de_cadastro():
    """RF12/D7: 'Higiene bucal' foi cadastrado antes e fica com a única escova."""
    escova, creme_dental, caixa, carrinho = _caixa_com_combo()
    fio_dental = Product("fio dental", ProductUnit.EACH)
    caixa.catalog.add_product(fio_dental, 5.0)
    caixa.add_combo_offer(Combo("Kit fio", {escova: 1.0, fio_dental: 1.0}))
    carrinho.add_item_quantity(escova, 1.0)
    carrinho.add_item_quantity(creme_dental, 1.0)
    carrinho.add_item_quantity(fio_dental, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    assert [d.product.name for d in recibo.discounts] == ["Higiene bucal"]
    assert recibo.total_price() == pytest.approx(27.5)


def test_combo_com_produto_por_quilo_conta_combos_inteiros():
    """D2: 1,5 kg de maçã exigindo 1,0 kg forma 1 combo; o 0,5 kg paga preço normal."""
    maca = Product("maçã", ProductUnit.KILO)
    escova = Product("escova", ProductUnit.EACH)
    catalogo = FakeCatalog()
    catalogo.add_product(maca, 8.0)
    catalogo.add_product(escova, 10.0)
    caixa = Teller(catalogo, combo_promotion=ComboPromotion())
    caixa.add_combo_offer(Combo("Lanche", {maca: 1.0, escova: 1.0}))
    carrinho = ShoppingCart()
    carrinho.add_item_quantity(maca, 1.5)
    carrinho.add_item_quantity(escova, 1.0)

    recibo = caixa.checks_out_articles_from(carrinho)

    # 1,5 × 8,00 + 10,00 = 22,00; desconto = 10% de (8,00 + 10,00) = 1,80
    assert [d.discount_amount for d in recibo.discounts] == pytest.approx([-1.8])
    assert recibo.total_price() == pytest.approx(20.2)


def test_recibo_impresso_mostra_a_linha_do_combo():
    """D6: a linha de desconto aparece como '10% combo (Higiene bucal)'."""
    escova, creme_dental, caixa, carrinho = _caixa_com_combo()
    carrinho.add_item_quantity(escova, 1.0)
    carrinho.add_item_quantity(creme_dental, 1.0)

    impresso = ReceiptPrinter().print_receipt(caixa.checks_out_articles_from(carrinho))

    linha_combo = "10% combo (Higiene bucal)" + " " * 10 + "-2.50\n"
    assert linha_combo in impresso
    assert impresso.endswith("Total: " + " " * 28 + "22.50\n")
