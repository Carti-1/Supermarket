"""Testes unitários do ComboPromotion, sem caixa nem carrinho.

O cálculo recebe direto as quantidades disponíveis (as que sobraram das ofertas
antigas). Preços do enunciado: escova R$ 10,00 e creme dental R$ 15,00.
"""
import pytest

from model_objects import Combo, Product, ProductUnit
from offers.combo_promotion import ComboPromotion
from tests.fake_catalog import FakeCatalog

ESCOVA = Product("escova", ProductUnit.EACH)
CREME = Product("creme dental", ProductUnit.EACH)
FIO = Product("fio dental", ProductUnit.EACH)
MACA = Product("maçã", ProductUnit.KILO)

HIGIENE = Combo("Higiene bucal", {ESCOVA: 1.0, CREME: 1.0})


@pytest.fixture
def catalogo():
    catalogo = FakeCatalog()
    catalogo.add_product(ESCOVA, 10.0)
    catalogo.add_product(CREME, 15.0)
    catalogo.add_product(FIO, 5.0)
    catalogo.add_product(MACA, 8.0)
    return catalogo


def _valores(descontos):
    return [desconto.discount_amount for desconto in descontos]


@pytest.mark.parametrize(
    "quantidades,esperado",
    [
        ({ESCOVA: 1.0, CREME: 1.0}, [-2.5]),           # RF07 combo completo
        ({ESCOVA: 1.0}, []),                           # RF08 falta o creme
        ({ESCOVA: 1.0, CREME: 0.0}, []),               # RF08 creme todo usado por oferta antiga
        ({ESCOVA: 2.0, CREME: 2.0}, [-2.5, -2.5]),     # RF09 dois conjuntos
        ({ESCOVA: 2.0, CREME: 1.0}, [-2.5]),           # RF10 escova excedente
        ({ESCOVA: 3.0, CREME: 2.0}, [-2.5, -2.5]),     # RF10 o mais escasso limita
        ({}, []),                                      # carrinho vazio
    ],
)
def test_calcula_um_desconto_por_combo_completo(catalogo, quantidades, esperado):
    descontos = ComboPromotion().calculate_discounts([HIGIENE], quantidades, catalogo)

    assert _valores(descontos) == pytest.approx(esperado)


def test_sem_combos_cadastrados_nao_ha_desconto(catalogo):
    assert ComboPromotion().calculate_discounts([], {ESCOVA: 1.0, CREME: 1.0}, catalogo) == []


def test_nao_altera_o_dicionario_recebido(catalogo):
    quantidades = {ESCOVA: 2.0, CREME: 2.0}

    ComboPromotion().calculate_discounts([HIGIENE], quantidades, catalogo)

    assert quantidades == {ESCOVA: 2.0, CREME: 2.0}


def test_combo_que_exige_mais_de_uma_unidade(catalogo):
    """2 escovas + 1 creme = R$ 35,00 por combo; com 5 escovas só cabem 2 combos."""
    combo = Combo("Família", {ESCOVA: 2.0, CREME: 1.0})

    descontos = ComboPromotion().calculate_discounts(
        [combo], {ESCOVA: 5.0, CREME: 3.0}, catalogo
    )

    assert _valores(descontos) == pytest.approx([-3.5, -3.5])


def test_combos_sobrepostos_respeitam_a_ordem_de_cadastro(catalogo):
    """RF12/D7: os dois combos querem a única escova; o primeiro da lista vence."""
    kit_fio = Combo("Kit fio", {ESCOVA: 1.0, FIO: 1.0})
    quantidades = {ESCOVA: 1.0, CREME: 1.0, FIO: 1.0}

    higiene_primeiro = ComboPromotion().calculate_discounts(
        [HIGIENE, kit_fio], quantidades, catalogo
    )
    kit_primeiro = ComboPromotion().calculate_discounts(
        [kit_fio, HIGIENE], quantidades, catalogo
    )

    assert [d.product.name for d in higiene_primeiro] == ["Higiene bucal"]
    assert _valores(higiene_primeiro) == pytest.approx([-2.5])
    assert [d.product.name for d in kit_primeiro] == ["Kit fio"]
    assert _valores(kit_primeiro) == pytest.approx([-1.5])


def test_combos_independentes_sao_aplicados_juntos(catalogo):
    """Com unidades para os dois, cada combo recebe seu próprio desconto."""
    kit_fio = Combo("Kit fio", {ESCOVA: 1.0, FIO: 1.0})

    descontos = ComboPromotion().calculate_discounts(
        [HIGIENE, kit_fio], {ESCOVA: 2.0, CREME: 1.0, FIO: 1.0}, catalogo
    )

    assert _valores(descontos) == pytest.approx([-2.5, -1.5])


@pytest.mark.parametrize(
    "quilos,combos_esperados",
    [(0.9, 0), (1.0, 1), (1.5, 1), (2.0, 2)],
)
def test_produto_por_quilo_conta_somente_combos_inteiros(catalogo, quilos, combos_esperados):
    """D2: 1,0 kg de maçã (R$ 8,00) + 1 escova (R$ 10,00) = R$ 18,00 → −1,80."""
    combo = Combo("Lanche", {MACA: 1.0, ESCOVA: 1.0})

    descontos = ComboPromotion().calculate_discounts(
        [combo], {MACA: quilos, ESCOVA: 5.0}, catalogo
    )

    assert _valores(descontos) == pytest.approx([-1.8] * combos_esperados)


def test_rotulo_do_desconto_usa_o_nome_do_combo(catalogo):
    """D6: o Discount precisa de um Product; usamos um com o nome do combo."""
    (desconto,) = ComboPromotion().calculate_discounts(
        [HIGIENE], {ESCOVA: 1.0, CREME: 1.0}, catalogo
    )

    assert desconto.product.name == "Higiene bucal"
    assert desconto.description == "10% combo"
