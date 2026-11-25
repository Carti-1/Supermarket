# Supermarket Receipt: Modernização de Sistema Legado

Trabalho prático da AV3 de **Alta Qualidade de Software** (SENAI CIMATEC, Prof. Leonardo Cardia).

A equipe atuou como uma consultoria técnica contratada para **modernizar de forma incremental** o sistema de caixa de um supermercado: entender o código legado, documentar requisitos e riscos, criar testes de caracterização, refatorar com padrões de projeto **sem alterar as regras comerciais existentes**, implementar uma nova promoção de **combos de produtos** e avaliar a segurança com **Bandit, pip-audit e Safety**.

> Projeto-base: [SupermarketReceipt-Refactoring-Kata](https://github.com/emilybache/SupermarketReceipt-Refactoring-Kata), de Emily Bache (licença MIT), versão `python_pytest`.

---

## Sumário

1. [O sistema](#1-o-sistema)
2. [Requisitos de ambiente](#2-requisitos-de-ambiente)
3. [Instalação](#3-instalação)
4. [Como rodar os testes](#4-como-rodar-os-testes)
5. [Cobertura de testes](#5-cobertura-de-testes)
6. [Análises de segurança](#6-análises-de-segurança)
7. [Estrutura de pastas](#7-estrutura-de-pastas)
8. [Arquitetura e decisões](#8-arquitetura-e-decisões)
9. [Documentação](#9-documentação)
10. [Fluxo de trabalho da equipe](#10-fluxo-de-trabalho-da-equipe)
11. [Equipe](#11-equipe)
12. [Créditos e licença](#12-créditos-e-licença)

---

## 1. O sistema

O caixa (`Teller`) recebe um carrinho, consulta os preços no catálogo, aplica as ofertas e emite um recibo com os itens, os descontos e o total.

**Ofertas legadas (preservadas):**

| Oferta | Regra |
|---|---|
| 3 por 2 | A cada 3 unidades, uma sai de graça |
| Desconto percentual | Percentual sobre toda a quantidade do produto |
| 2 por valor fixo | Cada par sai pelo valor fixo; a unidade avulsa paga preço cheio |
| 5 por valor fixo | Cada grupo de 5 sai pelo valor fixo; o resto paga preço cheio |

**Nova regra: combos promocionais.** Quando o cliente leva todos os produtos de um combo, recebe **10% de desconto apenas sobre os itens dos combos completos**.

| Compra | Resultado |
|---|---|
| 1 escova + 1 creme dental | 10% sobre os dois produtos |
| 2 escovas + 1 creme dental | Desconto em 1 combo; a escova a mais paga preço normal |
| 2 escovas + 2 cremes dentais | Desconto em 2 combos |
| Somente 1 escova | Sem desconto de combo |
| Produto que já tem outra oferta | A oferta antiga é aplicada primeiro; o combo usa só as unidades que sobraram (sem desconto duplicado) |

---

## 2. Requisitos de ambiente

| Item | Versão |
|---|---|
| Python | **3.10 ou superior** (o código usa a sintaxe `X \| None`). Testado com 3.12.10; análises de segurança registradas com 3.14.7 |
| Git | qualquer versão recente |
| Sistema | Windows (PowerShell) ou Linux/macOS (bash) |

As dependências do projeto estão em `requirements.txt` (`pytest`, `approvaltests`, `pytest-approvaltests`, `coverage`). As ferramentas de análise (Bandit, pip-audit, Safety, Radon) são instaladas **só localmente** e não entram no `requirements.txt`.

---

## 3. Instalação

### Windows (PowerShell)

```powershell
git clone https://github.com/Carti-1/Supermarket.git
cd Supermarket

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se o `Activate.ps1` falhar com erro de *execution policy*, libere a execução **só para o terminal atual** e tente de novo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Com o ambiente ativo, o prompt começa com `(.venv)`.

### Linux / macOS (bash)

```bash
git clone https://github.com/Carti-1/Supermarket.git
cd Supermarket

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## 4. Como rodar os testes

Com a `.venv` ativa, na raiz do projeto:

```powershell
python -m pytest -q
```

O `pytest.ini` já adiciona `src/` e `tests/` ao caminho de importação, então não é preciso configurar nada.

**Resultado esperado (25/11/2026):** `116 passed`, sem falhas e sem `xfail`.

Os testes de combo foram escritos antes da implementação (TDD) e ficaram marcados como `xfail(strict=True)`. Quando o `Teller` passou a aplicar combos por padrão, eles passaram (`XPASS(strict)`) e a marcação foi removida.

Rodar um grupo específico:

```powershell
python -m pytest tests/test_supermarket.py -v           # testes originais do kata (não alterados)
python -m pytest tests/test_comportamento_legado.py -v  # caracterização do comportamento legado
python -m pytest tests/test_estrategias.py -v           # estratégias de oferta (Strategy)
python -m pytest tests/test_fabrica_ofertas.py -v       # fábrica de estratégias (Factory)
python -m pytest tests/test_combos.py -v                # combos promocionais
```

---

## 5. Cobertura de testes

```powershell
python -m coverage run -m pytest -q
python -m coverage report -m
```

O relatório de cobertura e as evidências de execução ficam em `docs/evidencias_testes` e `docs/evidencias/`.

---

## 6. Análises de segurança

As três ferramentas foram executadas **antes** e **depois** da modernização. Resultados, versões, triagem e limitações estão em [`docs/seguranca_antes_depois`](docs/).

Instalação local (fora do `requirements.txt`):

```powershell
python -m pip install bandit pip-audit safety
```

| Ferramenta | O que analisa | Comando |
|---|---|---|
| Bandit | Padrões inseguros no código Python | `python -m bandit -r src` e `python -m bandit -r src tests` |
| pip-audit | Vulnerabilidades conhecidas nas dependências | `python -m pip_audit -r requirements.txt` |
| Safety | Vulnerabilidades conhecidas nas dependências (usa `.safety-policy.yml`) | `safety scan` |

Os comandos exatos, as versões das ferramentas e os resultados de cada execução estão registrados em [`docs/seguranca_antes_depois.txt`](docs/seguranca_antes_depois.txt).

**Observações:**
- Os alertas do Bandit em `tests/` são `B101 (assert_used)`, esperados em testes com pytest, e não indicam vulnerabilidade da aplicação.
- O Safety pode exigir login ou conta. As tentativas e as limitações estão registradas no relatório.
- Ausência de alertas não é prova de segurança total: cada ferramenta tem cobertura própria.

---

## 7. Estrutura de pastas

```text
Supermarket/
├── README.md                    # este arquivo
├── requirements.txt             # dependências do projeto (inalterado em relação ao kata)
├── pytest.ini                   # configuração do pytest (src/ e tests/ no caminho)
├── .safety-policy.yml           # política do Safety (exclui .venv/ e venv/)
├── src/
│   ├── model_objects.py         # entidades: Product, Offer, Discount, SpecialOfferType, Combo
│   ├── interfaces.py            # contratos (Protocol): catálogo, recibo, carrinho, estratégias, combo
│   ├── catalog.py               # catálogo de produtos
│   ├── shopping_cart.py         # carrinho: itens e aplicação das ofertas legadas
│   ├── receipt.py               # recibo: itens, descontos e total
│   ├── teller.py                # caixa: caso de uso "fechar a compra"
│   └── offers/
│       ├── legacy_strategies.py # Strategy: uma classe por oferta legada
│       ├── offer_factory.py     # Factory: escolhe a estratégia pelo tipo de oferta
│       └── combo_promotion.py   # Combos: 10% sobre conjuntos completos
├── tests/
│   ├── test_supermarket.py           # testes originais do kata (não editados)
│   ├── test_comportamento_legado.py  # testes de caracterização
│   ├── test_ofertas_legadas.py       # ofertas legadas
│   ├── test_estrategias.py           # estratégias (Strategy)
│   ├── test_fabrica_ofertas.py       # fábrica (Factory)
│   ├── test_interfaces.py            # contratos
│   ├── test_combos.py                # combos promocionais
│   ├── fake_catalog.py               # catálogo em memória para testes
│   └── receipt_printer.py            # impressão do recibo (usada nos testes)
├── docs/                        # diagnóstico, requisitos, plano, padrões, segurança, evidências
└── apresentacao/                # slides da defesa
```

---

## 8. Arquitetura e decisões

**Padrões de projeto aplicados**

| Padrão | Onde | Problema que resolve |
|---|---|---|
| **Strategy** | `src/offers/legacy_strategies.py` | O cálculo de cada oferta estava numa cadeia de `if/elif` dentro do carrinho; cada regra virou uma classe com `apply` |
| **Factory** (Simple Factory) | `src/offers/offer_factory.py` | Alguém precisa decidir "qual estratégia para este tipo?"; a fábrica concentra essa escolha num registro, e o carrinho não volta a ter `if/elif` |

**Princípios e decisões**

- **Contratos com `Protocol`** (`src/interfaces.py`): as classes dependem de portas, não de implementações concretas (DIP). Leitura e escrita do catálogo e do recibo ficam em portas separadas (ISP).
- **Injeção de dependência no `Teller`**: o calculador de combos é recebido pelo construtor, o que permite usar dublês nos testes.
- **D1, convivência de ofertas:** as ofertas legadas são aplicadas primeiro e o combo usa só as unidades que sobraram, para não dar desconto duplicado.
- **D4, busca por nome:** o catálogo ganhou `product_by_name`, e o `Teller` deixou de depender de um atributo interno do catálogo de testes (LSP).
- **D7, combos sobrepostos:** a ordem de cadastro dos combos define a prioridade.
- **D2, produtos por quilo em combos:** contam só combos inteiros (1,5 kg exigindo 1,0 kg forma 1 combo).
- **D3, defeito legado do "2 for X":** mantido de propósito, para preservar o comportamento existente.
- **D6, linha do combo no recibo:** impressa como "10% combo (nome do combo)".
- **Interfaces públicas preservadas:** `Teller(catalog)`, `checks_out_articles_from`, `ShoppingCart.add_item`… continuam com as mesmas assinaturas. As mudanças compatíveis estão justificadas no plano de contingência.

Detalhes, diagramas e trechos antes/depois estão nos documentos da seção 9.

---

## 9. Documentação

Tudo em [`docs/`](docs/):

| Documento | Conteúdo |
|---|---|
| [`requisitos.md`](docs/requisitos.md) | Requisitos RF/RNF com critérios de aceitação (inclui combos) |
| [`plano_contingencia.md`](docs/plano_contingencia.md) | Sequência das mudanças, invariantes, interfaces congeladas, riscos, reversão e decisões |
| [`seguranca_antes_depois.txt`](docs/seguranca_antes_depois.txt) | Bandit, pip-audit e Safety: comandos, versões, triagem e comparação |
| [`evidencias/`](docs/evidencias/) | Logs brutos das execuções (caracterização antes/depois) |
| `diagnostico_tecnico` | Code smells, riscos e evidências no código legado |
| `padroes_projeto` | Strategy e Factory: problema, diagrama, trechos antes/depois, SOLID |
| `evidencias_testes` | Execução dos testes antes/depois, cobertura e rastreabilidade |

Os documentos sem link são integrados pelos respectivos responsáveis na entrega final.

---

## 10. Fluxo de trabalho da equipe

- Cada tarefa numa branch própria, criada a partir da `develop` atualizada: `feature/…`, `test/…`, `docs/…`, `refactor/…`.
- Integração **só por Pull Request**, aprovado por outro membro; a `main` recebe a `develop` na entrega final.
- **Conventional Commits** em português: `test:`, `refactor:` (não muda comportamento), `feat:` (funcionalidade nova), `fix:` (defeito, em commit separado), `docs:`, `chore:`.
- Proibido `git push --force` e `git reset --hard` em `develop`/`main`. Para desfazer, usa-se `git revert`.
- `tests/test_supermarket.py` não é editado: é a prova original de preservação de comportamento.

---

## 11. Equipe

| Integrante | Responsabilidade principal |
|---|---|
| Heitor | Testes de caracterização, recibo, evidências de teste |
| João Pedro | Contratos (interfaces), diagnóstico técnico, análises de segurança |
| Lucca | Requisitos e combos promocionais |
| Matheus Sobral Imbassahy Cruz | Fábrica de estratégias, integração dos combos no `Teller`, plano de contingência, README |
| Pedro Prietto | Estratégias de oferta, carrinho, padrões de projeto, coordenação da integração |

---

## 12. Créditos e licença

- Kata original: **Supermarket Receipt Refactoring Kata**, de Emily Bache, distribuído sob a **licença MIT**: https://github.com/emilybache/SupermarketReceipt-Refactoring-Kata
- Modernização: equipe da AV3, Alta Qualidade de Software, SENAI CIMATEC, 2026.
