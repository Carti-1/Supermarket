"""Promoção de combos: 10% sobre os itens que formam conjuntos completos.

Implementa o contrato ComboPromotionPort (src/interfaces.py). É uma classe nova:
as ofertas antigas e o carrinho não foram editados para o combo existir (OCP).
Requisitos atendidos: RF07 a RF12 (docs/requisitos.md).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from interfaces import CatalogReaderPort, ComboPromotionPort
from model_objects import Combo, Discount, Product, ProductUnit


class ComboPromotion(ComboPromotionPort):
    """Aplica 10% sobre conjuntos completos, usando só as quantidades que sobraram."""

    def calculate_discounts(
        self,
        combos: Sequence[Combo],
        available_quantities: Mapping[Product, float],
        catalog: CatalogReaderPort,
    ) -> list[Discount]:
        # Cópia: o dicionário recebido é só para leitura (contrato da porta).
        remaining = dict(available_quantities)
        discounts: list[Discount] = []

        # A ordem recebida é a ordem de cadastro no caixa e define a prioridade
        # entre combos que disputam o mesmo produto (decisão D7).
        for combo in combos:
            complete = self._complete_sets(combo, remaining)
            if complete == 0:
                continue  # combo incompleto não recebe desconto (RF08)

            combo_price = sum(
                catalog.unit_price(product) * required
                for product, required in combo.required_quantities.items()
            )
            amount = combo_price * combo.discount_percentage / 100.0

            # Discount exige um Product; o combo tem vários, então a linha é
            # rotulada com um Product que só carrega o nome do combo (decisão D6).
            label = Product(combo.name, ProductUnit.EACH)
            description = f"{combo.discount_percentage:g}% combo"
            # Uma linha por combo completo (RF09).
            for _ in range(complete):
                discounts.append(Discount(label, description, -amount))

            # Consome as unidades usadas para que o próximo combo não as reutilize.
            # O que sobrar (excedente) fica com preço normal (RF10).
            for product, required in combo.required_quantities.items():
                remaining[product] -= required * complete

        return discounts

    @staticmethod
    def _complete_sets(combo: Combo, remaining: Mapping[Product, float]) -> int:
        """Quantos conjuntos inteiros cabem: o produto mais escasso limita.

        A divisão inteira (//) aceita quantidades fracionárias, como quilos
        (decisão D2): 1,5 kg com 1,0 kg exigido forma 1 combo. Produto ausente
        conta como 0, o que zera o resultado.
        """
        return min(
            int(remaining.get(product, 0.0) // required)
            for product, required in combo.required_quantities.items()
        )
