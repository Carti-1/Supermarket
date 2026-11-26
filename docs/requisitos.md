# Documento de Requisitos

**Projeto:** Modernização do Supermarket Receipt (AV3, Alta Qualidade de Software)
**Responsável pelo documento:** Lucca
**Repositório:** github.com/Carti-1/Supermarket (branch de integração: `develop`)
**Versão:** 1.0 (24/11/2026)

Este documento descreve o comportamento que o sistema **já tinha** (ofertas legadas e recibo) e a **nova regra de negócio** (combos promocionais). Cada requisito tem um identificador, um critério de aceitação verificável e o teste que o comprova. Os IDs são citados no plano de contingência (`docs/plano_contingencia.md`).

Valores usados nos exemplos (os mesmos dos testes):

| Produto | Unidade | Preço |
|---|---|---|
| escova | unidade | R$ 10,00 |
| creme dental | unidade | R$ 15,00 |
| fio dental | unidade | R$ 5,00 |
| maçã | quilo | R$ 8,00/kg |

Nos testes de caracterização das ofertas legadas, o produto de teste custa R$ 10,00.

---

## 1. Requisitos funcionais

### 1.1 Comportamento legado (deve ser preservado)

Os valores esperados destes requisitos **não foram inventados**: são os obtidos rodando o código original (caracterização do Heitor, `docs/evidencias/caracterizacao_codigo_original.txt`).

| ID | Requisito | Critério de aceitação | Teste |
|---|---|---|---|
| RF01 | **3 por 2** (`THREE_FOR_TWO`): a cada grupo de 3 unidades, uma sai de graça. Com 2 ou menos não há desconto. | 3 un. → total 20,00, desconto −10,00 · 4 un. → 30,00 · 2 un. → 20,00 sem desconto · descrição `"3 for 2"` | `test_comportamento_legado.py::test_tres_por_dois_com_varios_grupos`, `test_estrategias.py::test_tres_por_dois` |
| RF02 | **Desconto percentual** (`TEN_PERCENT_DISCOUNT`): `quantidade × preço × argumento / 100` sobre **toda** a quantidade, inclusive por quilo. | 1 un. com 10% → total 9,00, desconto −1,00 · descrição `"10.0% off"` | `test_comportamento_legado.py::test_dez_por_cento_de_desconto`, `::test_dez_por_cento_em_produto_por_quilo` |
| RF03 | **2 por valor fixo** (`TWO_FOR_AMOUNT`): com menos de 2 unidades não há desconto. Mantém a fórmula do legado, inclusive o defeito D3 (seção 3). | 2 un. "2 for 15" → 15,00, desconto −5,00 · 3 un. → 32,50 (desconto **+2,50**, D3) · descrição `"2 for 15.0"` | `test_comportamento_legado.py::test_dois_por_valor_com_quantidade_par`, `::test_dois_por_valor_com_quantidade_impar_registra_defeito_do_legado` |
| RF04 | **5 por valor fixo** (`FIVE_FOR_AMOUNT`): a cada grupo de 5 cobra o valor fixo; o resto paga preço cheio. | 5 un. "5 for 40" → 40,00, desconto −10,00 · 4 un. → 40,00 sem desconto · 11 un. → 90,00 | `test_comportamento_legado.py::test_cinco_por_valor_com_varios_grupos` |
| RF05 | **Checkout sem oferta** soma `preço × quantidade` de cada item, sem desconto. Carrinho vazio tem total 0. | 2 un. de R$ 10,00 → total 20,00, nenhum desconto · carrinho vazio → total 0, nenhuma linha | `test_comportamento_legado.py::test_sem_oferta_nao_gera_desconto`, `::test_carrinho_vazio_tem_total_zero_e_nenhuma_linha`, `test_supermarket.py` |
| RF06 | **Recibo** lista os itens (com quantidade e preço unitário), os descontos como valores negativos com descrição e produto, e o total = soma dos itens + soma dos descontos. | Saída do `ReceiptPrinter` igual à aprovada; linha de desconto `"<descrição> (<produto>)"` | `test_comportamento_legado.py::test_descricao_e_produto_de_cada_desconto`, `::test_campos_do_item_do_recibo` |

### 1.2 Combos promocionais (nova regra de negócio)

Um **combo** é um conjunto definido de produtos com a quantidade exigida de cada um (`Combo(nome, {produto: quantidade})`). Quando o carrinho tem todos os produtos de um combo, aplica-se **10%** de desconto **somente** sobre o valor dos itens que formam combos completos.

| ID | Requisito | Critério de aceitação | Teste |
|---|---|---|---|
| RF07 | **Combo completo** recebe 10% sobre o valor dos seus itens. | 1 escova + 1 creme → desconto −2,50; total 22,50 | `test_combos.py::test_cenarios_do_enunciado_com_combo_injetado[1.0-1.0-...]`, `test_combo_promotion.py::test_calcula_um_desconto_por_combo_completo` |
| RF08 | **Combo incompleto** não recebe desconto. | Só 1 escova → total 10,00, nenhum desconto | `test_combos.py::test_combo_incompleto_nao_concede_desconto`, `::test_cenarios_do_enunciado_com_combo_injetado[1.0-0.0-...]` |
| RF09 | **Cada repetição completa** gera um desconto próprio (uma linha por combo). | 2 escovas + 2 cremes → 2 linhas de −2,50; total 45,00 | `test_combos.py::test_cenarios_do_enunciado_com_combo_injetado[2.0-2.0-...]`, `test_combo_promotion.py` |
| RF10 | **Unidades excedentes** ficam com preço normal. O número de combos é limitado pelo produto mais escasso. | 2 escovas + 1 creme → 1 combo; total 32,50 · 3 escovas + 2 cremes → 2 combos | `test_combos.py::test_cenarios_do_enunciado_com_combo_injetado[2.0-1.0-...]`, `test_combo_promotion.py::test_calcula_um_desconto_por_combo_completo` |
| RF11 | **Convivência com ofertas legadas (D1):** a oferta antiga é aplicada primeiro; o combo usa só as unidades que **sobraram**. Nenhuma unidade recebe dois descontos. | 4 escovas (3 por 2) + 1 creme → −10,00 e −2,50; total 42,50 · escova com 10% + 1 creme → só −1,00; total 24,00 · 3 escovas ("2 for 15") + 1 creme → +2,50 (D3) e −2,50; total 45,00 | `test_combos.py::test_tres_por_dois_tem_prioridade_e_combo_usa_a_sobra`, `::test_dez_por_cento_individual_reserva_toda_a_quantidade`, `::test_dois_por_valor_reserva_duas_escovas_e_a_terceira_entra_no_combo`, `::test_caixa_entrega_ao_calculador_somente_quantidades_restantes` |
| RF12 | **Combos sobrepostos (D7):** quando dois combos disputam a mesma unidade, vence o cadastrado primeiro. Unidades já usadas por um combo não entram em outro. | Combos "Higiene bucal" (escova + creme) e depois "Kit fio" (escova + fio); carrinho com 1 de cada → só "Higiene bucal" (−2,50); total 27,50. Invertendo a ordem → só "Kit fio" (−1,50) | `test_combos.py::test_combos_que_disputam_a_mesma_escova_seguem_a_ordem_de_cadastro`, `test_combo_promotion.py::test_combos_sobrepostos_respeitam_a_ordem_de_cadastro` |
| RF13 | **Busca de produto por nome (D4):** o catálogo devolve o produto pelo nome, ou `None` se não existir. | `product_with_name("cafe")` → o produto; nome inexistente → `None` | `test_interfaces.py::test_caixa_usa_as_interfaces_de_catalogo_carrinho_e_recibo`, `::test_fake_catalog_implementa_as_portas_de_leitura_e_escrita` |
| RF14 | **Combo com produto por quilo (D2):** é permitido; contam-se só combos inteiros. | Maçã 1,5 kg (exige 1,0 kg) + 1 escova → 1 combo de −1,80; total 20,20 · 0,9 kg → nenhum combo | `test_combos.py::test_combo_com_produto_por_quilo_conta_combos_inteiros`, `test_combo_promotion.py::test_produto_por_quilo_conta_somente_combos_inteiros` |
| RF15 | **Rótulo do desconto de combo (D6):** a linha do recibo mostra o percentual e o nome do combo. | Recibo impresso contém `10% combo (Higiene bucal)` com `-2.50` | `test_combos.py::test_recibo_impresso_mostra_a_linha_do_combo`, `test_combo_promotion.py::test_rotulo_do_desconto_usa_o_nome_do_combo` |
| RF16 | **Combo válido:** o combo precisa de nome, de ao menos um produto e de quantidades positivas. | Nome vazio, composição vazia ou quantidade ≤ 0 → `ValueError` | `test_combos.py::test_combo_rejeita_definicoes_sem_composicao_valida` |

---

## 2. Requisitos não funcionais

| ID | Requisito | Critério de aceitação | Evidência |
|---|---|---|---|
| RNF01 | **Compatibilidade:** as interfaces públicas do legado são preservadas (`Teller(catalog)`, `add_special_offer`, `checks_out_articles_from`, `ShoppingCart`, `Receipt`, `model_objects`). | `tests/test_supermarket.py` **inalterado** e verde; testes de caracterização rodam iguais antes e depois | `git log -- tests/test_supermarket.py`; `pytest` |
| RNF02 | **Extensibilidade (OCP):** uma nova modalidade de promoção entra sem editar o carrinho nem as ofertas antigas. | `ComboPromotion` está em arquivo novo (`src/offers/combo_promotion.py`) e `shopping_cart.py` não foi alterado para o combo funcionar | `git log -- src/shopping_cart.py` |
| RNF03 | **Ambiente reprodutível:** qualquer pessoa instala e roda os testes do zero. | README com `python -m venv`, `pip install -r requirements.txt` e `python -m pytest` | `README.md` |
| RNF04 | **Sem dependências novas desnecessárias.** | `requirements.txt` igual ao original; Bandit/pip-audit/Safety instalados só localmente | `git diff main -- requirements.txt` |
| RNF05 | **Segurança analisada antes e depois** com Bandit, pip-audit e Safety. | Relatório com versões, comandos, achados, triagem e comparação | `docs/seguranca_antes_depois.txt` |
| RNF06 | **Testabilidade:** o cálculo de combos pode ser testado isolado, sem caixa nem banco. | `ComboPromotion().calculate_discounts(...)` testado só com `FakeCatalog` e um dicionário | `tests/test_combo_promotion.py` |
| RNF07 | **Imutabilidade da entrada:** o cálculo de combos não altera as quantidades que recebe. | Dicionário recebido igual antes e depois da chamada | `test_combo_promotion.py::test_nao_altera_o_dicionario_recebido` |

---

## 3. Decisões de negócio

O enunciado exige "explicitar o tratamento de múltiplos combos e o critério de convivência com outras ofertas". As decisões abaixo respondem a isso.

### D1 — Convivência entre ofertas antigas e combos

**Decisão:** as ofertas legadas são aplicadas **primeiro**. `ShoppingCart.handle_offers` devolve as quantidades que cada oferta **não** usou, e só essas vão para o `ComboPromotion`.

- 3 por 2, 2 por X e 5 por X reservam apenas os grupos completos (4 escovas no 3 por 2 → 3 reservadas, 1 livre).
- O desconto percentual reserva **toda** a quantidade do produto (ele já desconta cada unidade).

**Por quê:** impede desconto duplicado no mesmo item (exigência do edital) e mantém os valores das ofertas antigas exatamente iguais (RNF01).
**Alternativa descartada:** escolher, por carrinho, a combinação mais vantajosa para o cliente. Muda os valores das ofertas antigas, é difícil de explicar no caixa e exige algoritmo de otimização sem pedido do cliente.

### D2 — Produto vendido por quilo no combo

**Decisão:** permitido. O combo guarda a quantidade exigida como `float` e o cálculo conta **só combos inteiros** (`int(quantidade // exigido)`). O que sobra paga preço normal.
**Exemplo:** combo exige 1,0 kg de maçã; o carrinho tem 1,5 kg → 1 combo; 0,5 kg a preço normal.
**Limitação conhecida:** quantidades fracionárias seguem a aritmética de ponto flutuante do Python, como o restante do legado.

### D3 — Defeito legado do "2 por X" (registrado, não é do combo)

Com 3 unidades de R$ 10,00 em "2 for 15" o legado cobra R$ 32,50 (mais que R$ 30,00 sem oferta). O valor foi caracterizado e **mantido**. O combo não corrige nem agrava o defeito: ele só usa a unidade que sobrou (RF11). Uma eventual correção vai em commit `fix:` separado, decidido em grupo.

### D4 — Busca de produto por nome

O catálogo ganhou `product_by_name`; `Teller.product_with_name` deixou de ler um atributo interno do `FakeCatalog` (corrige violação de LSP).

### D6 — Produto usado no desconto do combo

**Decisão:** `Discount` exige um `Product`, mas o combo tem vários. Usamos um `Product` com o **nome do combo**, só para rotular a linha. A descrição é `"10% combo"`, e o `ReceiptPrinter` imprime `10% combo (Higiene bucal)`.
**Por quê:** reaproveita `Discount` e `ReceiptPrinter` sem alterá-los. Esse `Product` de rótulo não está no catálogo nem no carrinho; ele não é usado para cálculo.

### D7 — Múltiplos combos e combos sobrepostos

**Decisão:** os combos são avaliados **na ordem de cadastro** (`Teller.add_combo_offer`). Cada combo consome as unidades que usou, então o próximo só enxerga o que sobrou. Combos que não disputam produtos são todos aplicados.
**Por quê:** regra simples, previsível e que o supermercado controla pela ordem de cadastro.
**Alternativa descartada:** procurar a combinação de combos de maior desconto. Mais complexa e sem pedido do cliente.

---

## 4. Algoritmo do combo (`src/offers/combo_promotion.py`)

1. Copia as quantidades recebidas (o dicionário original não é alterado — RNF07).
2. Percorre os combos na ordem recebida (D7).
3. Número de combos completos = **mínimo**, entre os produtos exigidos, de `int(disponível // exigido)`. É o mínimo porque o produto mais escasso limita quantos conjuntos inteiros existem; produto ausente conta como 0 (RF08, RF10).
4. Preço de um combo = soma de `preço unitário × quantidade exigida`; desconto = preço × 10 / 100, negativo (RF07).
5. Gera **uma linha de desconto por combo completo** (RF09).
6. Subtrai as quantidades usadas antes de avaliar o próximo combo (RF12).

---

## 5. Rastreabilidade resumida

| Requisito | Implementação | Teste |
|---|---|---|
| RF01–RF04 | `src/shopping_cart.py`, `src/offers/legacy_strategies.py` | `test_comportamento_legado.py`, `test_estrategias.py`, `test_ofertas_legadas.py` |
| RF05–RF06 | `src/teller.py`, `src/receipt.py`, `tests/receipt_printer.py` | `test_comportamento_legado.py`, `test_supermarket.py` |
| RF07–RF12, RF14–RF15 | `src/offers/combo_promotion.py` | `test_combo_promotion.py`, `test_combos.py` |
| RF11 (sobras) | `ShoppingCart.handle_offers` (retorno), `Teller.checks_out_articles_from` (ordem) | `test_combos.py`, `test_ofertas_legadas.py` |
| RF13 | `catalog.py`, `teller.py` | `test_interfaces.py` |
| RF16 | `model_objects.Combo` | `test_combos.py` |

## 6. Situação da integração

O `Teller` usa o `ComboPromotion` por padrão (PR #14): `Teller(catalogo)` já aplica combos, sem precisar injetar o calculador; a injeção continua possível para testes com dublê. Os 4 testes que estavam em `xfail(strict=True)` em `test_combos.py` passaram (`XPASS(strict)`) e os marcadores foram removidos. Suíte final: **116 passed, 0 xfail** (evidências em `docs/evidencias_testes.md`).
