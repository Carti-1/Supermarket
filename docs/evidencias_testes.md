# Evidências de Testes

**Projeto:** Modernização do Supermarket Receipt (AV3, Alta Qualidade de Software)
**Responsável pelo documento:** Heitor (registro executado por Matheus Sobral em 25/11/2026)
**Repositório:** github.com/Carti-1/Supermarket (branch de integração: `develop`)
**Versão:** 1.0 (25/11/2026)

Este documento reúne a prova de que a refatoração **preservou o comportamento legado** e de que a **nova regra de combos** funciona: execução antes e depois, cobertura e rastreabilidade de cada requisito até o teste que o comprova.

---

## 1. Ambiente

| Item | Versão |
|---|---|
| Sistema | Windows, PowerShell |
| Python | 3.12.10 |
| pytest | 9.2.0 |
| coverage | 7.17.4 |
| approvaltests | 21.0.0 |
| pytest-approvaltests | 0.2.4 |

Versões obtidas com `python --version` e `python -m pip freeze`, no ambiente virtual `.venv`, a partir do `requirements.txt` do projeto (inalterado em relação ao kata original).

Commit da execução "depois": `da81345` (merge do PR #15 na `develop`), com todo o código integrado: Strategy, Factory, combos e Teller.

---

## 2. Antes × depois

| Momento | O que rodou | Resultado |
|---|---|---|
| Código original do kata (`ff9b330`) | Testes que vieram com o projeto (`test_supermarket.py`) | 1 teste |
| Código original + caracterização | `tests/test_comportamento_legado.py` rodando sobre o código **original** | **34 passed** |
| Código atual + caracterização | O mesmo arquivo, sem nenhuma alteração, rodando sobre o código **refatorado** | **34 passed** |
| Entrega final (`da81345`) | Suíte completa | **116 passed, 0 failed, 0 xfail** |

**Leitura:** os mesmos 34 testes de caracterização passam no código original e no refatorado. Como eles fixam os valores, descontos, descrições e campos do recibo do legado, isso mostra que a refatoração não mudou o comportamento observável. Os demais testes (de 34 para 116) cobrem as peças novas: contratos, estratégias, fábrica e combos.

Logs completos:
- [`evidencias/caracterizacao_codigo_original.txt`](evidencias/caracterizacao_codigo_original.txt)
- [`evidencias/caracterizacao_codigo_atual.txt`](evidencias/caracterizacao_codigo_atual.txt)
- [`evidencias/pytest_depois.txt`](evidencias/pytest_depois.txt) (suíte completa, modo verboso)

---

## 3. Testes de caracterização

Testes de caracterização registram **o que o sistema faz hoje**, e não o que deveria fazer. Eles foram escritos **antes** de qualquer refatoração e executados primeiro no código original. Os valores esperados vieram dessa execução, não de suposições.

O que eles fixam (`tests/test_comportamento_legado.py`):

- os valores das 4 ofertas legadas (3 por 2, percentual, 2 por X, 5 por X), inclusive com produtos vendidos por quilo;
- carrinho sem oferta, carrinho vazio e oferta para produto fora do carrinho;
- mesmo produto adicionado duas vezes (duas linhas no recibo, oferta sobre a soma);
- vários produtos com ofertas diferentes no mesmo carrinho;
- **o texto e o produto de cada desconto** (`"3 for 2"`, `"10.0% off"`, `"2 for 15.0"`, `"5 for 40.0"`);
- os campos de cada item do recibo.

Depois de cada etapa da refatoração, o mesmo arquivo foi executado de novo, **sem alterações**. Se um valor mudasse, o teste falharia e o PR não seria integrado (plano de contingência, seção 7).

---

## 4. Defeito legado D3 (mantido de propósito)

Na oferta "2 por valor fixo", o código original usa divisão real (`/`) em vez de divisão inteira (`//`). Com 3 unidades de R$ 10,00 em "2 for 15":

```
15 × (3 / 2) + 1 × 10 = 32,50   →   "desconto" de +2,50 (cobra mais que os R$ 30,00 sem oferta)
```

O valor foi **caracterizado e mantido**, porque o enunciado exige preservar as regras comerciais existentes. Ele está registrado nos testes:

- `test_comportamento_legado.py::test_dois_por_valor_com_quantidade_impar_registra_defeito_do_legado`
- `test_combos.py::test_dois_por_valor_reserva_duas_escovas_e_a_terceira_entra_no_combo` (o combo usa só a unidade que sobrou e não corrige nem duplica o defeito)

Uma eventual correção seria feita num commit `fix:` separado, por decisão do grupo (decisão D3).

---

## 5. Caso "3 for 2": a caracterização funcionando

Ao extrair as ofertas em estratégias (padrão Strategy), a descrição da oferta "3 por 2" foi traduzida para **"3 por 2"**, mas o legado imprime **"3 for 2"**. O enunciado exige preservar os valores exibidos no recibo.

- **Proteção:** o teste `test_descricao_e_produto_de_cada_desconto[...-3 for 2]` fixa o texto original.
- **Correção:** o commit `647996d fix(ofertas): restaura descrição legada '3 for 2' da estratégia`, em commit `fix:` separado, como manda a regra da equipe, integrado junto com o PR #15, que faz o carrinho delegar às estratégias.

É exatamente o tipo de regressão que os testes de caracterização existem para pegar: uma mudança pequena, fácil de passar despercebida numa revisão, que alteraria o recibo do cliente.

---

## 6. TDD dos combos

Os testes de combo foram escritos **antes** da implementação e marcados com `@pytest.mark.xfail(strict=True)`:

| Etapa | Resultado |
|---|---|
| Contratos e testes de combo criados | 4 `xfailed` (fase vermelha, esperada) |
| `ComboPromotion` integrado (PR #13), ainda sem ligação no `Teller` | 112 passed, 4 xfailed |
| `Teller` passa a usar o `ComboPromotion` por padrão (PR #14) | **4 failed com `XPASS(strict)`**: os testes que "deviam falhar" passaram, e o `strict` obriga a remover a marcação |
| Marcações `xfail` removidas | **116 passed, 0 xfail** |

---

## 7. Cobertura

Comandos:

```powershell
python -m coverage run -m pytest
python -m coverage report -m
```

Resultado completo em [`evidencias/cobertura.txt`](evidencias/cobertura.txt). Código da aplicação (`src/`):

| Arquivo | Statements | Não cobertos | Cobertura | Linhas não cobertas |
|---|---|---|---|---|
| `src/catalog.py` | 10 | 3 | 70% | 10, 13, 16 |
| `src/interfaces.py` | 43 | 0 | 100% | — |
| `src/model_objects.py` | 40 | 0 | 100% | — |
| `src/offers/combo_promotion.py` | 24 | 0 | 100% | — |
| `src/offers/legacy_strategies.py` | 36 | 0 | 100% | — |
| `src/offers/offer_factory.py` | 16 | 0 | 100% | — |
| `src/receipt.py` | 30 | 0 | 100% | — |
| `src/shopping_cart.py` | 36 | 1 | 97% | 33 |
| `src/teller.py` | 30 | 0 | 100% | — |
| **Total `src/`** | **265** | **4** | **98,5%** | |
| **Total do relatório (`src/` + `tests/`)** | **840** | **10** | **99%** | |

**Linhas não cobertas:**

- **`src/catalog.py` (10, 13, 16):** catálogo "real" do kata, que representa o acesso a um banco de dados. Nos testes usa-se o `FakeCatalog` (em memória), justamente para não depender de banco. Não é lógica de negócio da refatoração.
- **`src/shopping_cart.py` (33):** o `return` da propriedade `product_quantities`, que faz parte da interface pública preservada, mas que nenhum teste lê diretamente (o carrinho usa o dicionário internamente).
- **`tests/receipt_printer.py` e linhas isoladas em arquivos de teste:** ramos auxiliares da impressão do recibo e métodos de dublês que não são chamados.

**Observação importante:** 99% de cobertura significa que quase todas as linhas **foram executadas** pelos testes, não que estão **corretas**. Uma linha pode rodar sem que nenhum `assert` confira seu resultado. A garantia de comportamento vem das asserções dos testes de caracterização e dos cenários de combo, não do número de cobertura em si.

---

## 8. Rastreabilidade: requisito → implementação → teste → resultado

Baseada na seção 5 de [`requisitos.md`](requisitos.md):

| Requisito | Implementação | Teste | Resultado |
|---|---|---|---|
| RF01–RF04 (ofertas legadas) | `src/shopping_cart.py`, `src/offers/legacy_strategies.py`, `src/offers/offer_factory.py` | `test_comportamento_legado.py`, `test_estrategias.py`, `test_ofertas_legadas.py`, `test_fabrica_ofertas.py` | ✅ passed |
| RF05–RF06 (checkout e recibo) | `src/teller.py`, `src/receipt.py`, `tests/receipt_printer.py` | `test_comportamento_legado.py`, `test_supermarket.py` | ✅ passed |
| RF07–RF12, RF14–RF15 (combos) | `src/offers/combo_promotion.py`, `src/teller.py` | `test_combo_promotion.py`, `test_combos.py` | ✅ passed |
| RF11 (sobras para o combo, D1) | `ShoppingCart.handle_offers` (retorno), `Teller.checks_out_articles_from` (ordem) | `test_combos.py`, `test_ofertas_legadas.py` | ✅ passed |
| RF13 (busca por nome, D4) | `src/catalog.py`, `src/teller.py` | `test_interfaces.py` | ✅ passed |
| RF16 (combo válido) | `model_objects.Combo` | `test_combos.py` | ✅ passed |
| RNF01 (interfaces preservadas) | assinaturas públicas mantidas | `test_supermarket.py` inalterado e verde; caracterização 34/34 antes e depois | ✅ passed |
| RNF02 (OCP) | combo em arquivo novo (`src/offers/combo_promotion.py`) | os commits do combo (`989c1d8`, `ae0f982`, `ac9c65e`) não alteram `src/shopping_cart.py`: conferível com `git log --oneline -- src/shopping_cart.py` | ✅ verificado |
| RNF06–RNF07 (combo testável e sem efeito colateral) | `ComboPromotion` | `test_combo_promotion.py` | ✅ passed |

---

## 9. Como reproduzir do zero

```powershell
git clone https://github.com/Carti-1/Supermarket.git
cd Supermarket
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Suíte completa (esperado: 116 passed)
python -m pytest -q

# Log detalhado e cobertura
python -m pytest -v 2>&1 | Out-File -Encoding utf8 docs\evidencias\pytest_depois.txt
python -m coverage run -m pytest
python -m coverage report -m 2>&1 | Out-File -Encoding utf8 docs\evidencias\cobertura.txt

# Só a caracterização (esperado: 34 passed)
python -m pytest tests/test_comportamento_legado.py -v
```

O arquivo `.coverage`, gerado pelo coverage, não é versionado.
