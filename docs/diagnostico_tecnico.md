# Diagnóstico técnico do legado

- **Projeto:** Modernização do Supermarket Receipt (AV3)
- **Data:** 25/11/2026
- **Código original:** `ff9b330` (`origin/main`)
- **Código atual analisado:** `5b73a5e` (`develop`, integração até o PR #18)
- **Responsável:** João Pedro Silva

## 1. Contexto

O projeto parte de um sistema legado de caixa que calcula o total de um carrinho,
aplica ofertas e monta um recibo. O objetivo da consultoria é modernizar sua
estrutura para facilitar manutenção, testes e inclusão da nova regra de combos,
preservando os resultados e as interfaces públicas do sistema anterior.

O diagnóstico compara o código original do repositório com a implementação
integrada em `develop`. A análise registra os problemas observados antes da
refatoração, a resposta dada pela equipe e os pontos que continuam conhecidos.
Em especial, o defeito legado D3 foi mantido de propósito para preservar o
comportamento caracterizado; não deve ser confundido com uma regressão da
refatoração.

## 2. Método

1. Leitura do código original no commit `ff9b330` e do código atual no commit
   `5b73a5e`.
2. Medição da complexidade ciclomática com Radon 6.0.1 nos dois códigos. A versão
   do Radon foi a mesma nas duas execuções.
3. Execução da suíte completa no código atual: `python -m pytest -q`.
4. Conferência das evidências de caracterização executadas no código original e
   depois da refatoração. O relatório existente registra 34 testes de
   caracterização aprovados em cada versão.

Os resultados completos do Radon estão em
[`evidencias/radon_cc_antes.txt`](evidencias/radon_cc_antes.txt) e
[`evidencias/radon_cc_depois.txt`](evidencias/radon_cc_depois.txt). A saída
detalhada da suíte atual está em
[`evidencias/pytest_depois.txt`](evidencias/pytest_depois.txt).

## 3. Achados

Os trechos da coluna “Exemplo original” são do commit `ff9b330`; as referências de
linha se referem a esse código.

## 3. Achados

Os trechos da coluna **Trecho original** foram extraídos do commit `ff9b330` (`origin/main`), e as referências de linha correspondem a essa versão.

### 3.1 Carrinho e Regras de Promoção (`shopping_cart.py`)

| Arquivo e linha | Trecho original | Problema e efeito | Situação após a refatoração |
| :--- | :--- | :--- | :--- |
| `shopping_cart.py:30-68` | `def handle_offers(self, receipt, offers, catalog):` seguido de cadeia de `if offer.offer_type == ...` | **Problema:** método longo concentrando seleção e cálculo de todas as ofertas (complexidade **C = 13**).<br>**Efeito:** viola **OCP** (cada nova oferta exige editar o carrinho) e dificulta testes unitários isolados. | O carrinho delega o cálculo às estratégias obtidas via `OfferStrategyFactory`. A complexidade de `handle_offers` caiu para **A (4)**, a regra de combos foi isolada em `src/offers/combo_promotion.py` e cada componente possui testes próprios. |
| `shopping_cart.py:6-28` e `30-68` | Atributos `_items` / `_product_quantities` na mesma classe de `handle_offers` | **Problema:** `ShoppingCart` armazena itens e também executa regras de desconto.<br>**Efeito:** viola **SRP** ao acumular duas razões distintas para mudar. | O carrinho mantém o estado dos itens e coordena a execução, enquanto cada regra legada foi extraída para sua própria classe de estratégia e o combo para módulo dedicado. |
| `shopping_cart.py:31, 38-52, 55, 64` | `for p ...`, `x = 1`, `x = 3`, `x = 2`, `x = 5`, `number_of_x` | **Problema:** identificadores abreviados (`p`, `x`) e números mágicos espalhados (`2`, `3`, `5`, `100`).<br>**Efeito:** leitura lenta e regras de negócio implícitas no cálculo. | As regras foram encapsuladas em classes descritivas (`ThreeForTwoStrategy`, `TwoForAmountStrategy`, etc.) com variáveis claras (`groups`, `charged`). Os tamanhos de grupo (`2`, `3`, `5`) permanecem locais às respectivas estratégias. |
| `shopping_cart.py:45` | `offer.argument * (quantity_as_int / x)` | **Problema:** divisão real (`/`) em vez de inteira (`//`) na oferta "2 por X" (**defeito D3**).<br>**Efeito:** 3 itens de R$ 10,00 na oferta "2 por 15" totalizam R$ 32,50 em vez de R$ 25,00. | Fórmula preservada intencionalmente em `TwoForAmountStrategy` e protegida por teste de caracterização para evitar regressão comportamental; eventual correção comercial exige decisão separada. |
| `shopping_cart.py:45-65` | Fórmulas paralelas para `SpecialOfferType.TWO_FOR_AMOUNT` e `FIVE_FOR_AMOUNT` | **Problema:** cálculos semelhantes para "2 por X" e "5 por X" duplicados no mesmo método.<br>**Efeito:** acoplamento entre ofertas distintas e risco de efeito colateral ao alterar uma regra. | Cada oferta legada possui estratégia independente, evitando unificação forçada de regras que têm comportamentos diferentes (especialmente devido ao defeito D3). |

### 3.2 Catálogo e Contratos (`teller.py` e `catalog.py`)

| Arquivo e linha | Trecho original | Problema e efeito | Situação após a refatoração |
| :--- | :--- | :--- | :--- |
| `teller.py:28-29` | `return self.catalog.products.get(name, None)` | **Problema:** `Teller.product_with_name` acessa o atributo interno `products`, existente apenas no `FakeCatalog`.<br>**Efeito:** viola **LSP** e quebra a substituição por outras implementações de catálogo. | `Teller.product_with_name` passou a invocar o método de contrato `CatalogReaderPort.product_by_name`, com cobertura de testes para produto encontrado e ausente. |
| `catalog.py:4-8` | `raise Exception("cannot be called from a unit test - it accesses the database")` | **Problema:** classe concreta (`SupermarketCatalog`) que apenas lança exceções genéricas.<br>**Efeito:** contrato implícito e impossibilidade de testar persistência de forma desacoplada. | Contratos formalizados nas interfaces `CatalogReaderPort` e `CatalogWriterPort`. `SupermarketCatalog` permanece como esqueleto sem banco real, enquanto os testes utilizam `FakeCatalog`. |

### 3.3 Suíte de Testes e Ambiente (`tests/` e `requirements.txt`)

| Arquivo e linha | Trecho original | Problema e efeito | Situação após a refatoração |
| :--- | :--- | :--- | :--- |
| `tests/test_supermarket.py` | Arquivo único contendo apenas 1 caso de teste sem ofertas | **Problema:** ausência de cobertura sobre ofertas, recibos e casos de borda.<br>**Efeito:** refatorar sem rede de segurança contra regressões. | Suíte expandida para **116 testes aprovados**, incluindo **34 testes de caracterização** validados tanto no código original quanto no refatorado. |
| `requirements.txt` | Dependências listadas sem pinagem de versão | **Problema:** ausência de versões fixas para os pacotes declarados.<br>**Efeito:** ambiente não reprodutível em instalações futuras. | Nenhuma nova dependência de aplicação foi adicionada (`radon` foi usado apenas localmente). A fixação de versões permanece registrada como pendência operacional. |

## 4. Métricas de complexidade

Radon 6.0.1 foi executado com `radon cc src -s -a` em ambos os estados. A
comparação principal é do mesmo método, `ShoppingCart.handle_offers`:

| Estado | Complexidade ciclomática | Nota Radon | Interpretação |
|---|---:|---|---|
| Original (`ff9b330`) | 13 | C | Muitos caminhos condicionais em uma única rotina de ofertas. |
| Atual (`5b73a5e`) | 4 | A | O método coordena as ofertas e delega cada regra à estratégia correspondente. |

A queda de C (13) para A (4) confirma a redução de complexidade local que motivou
a extração das estratégias. O relatório global de Radon também mostra novas
classes e módulos, portanto a média geral dos dois projetos não deve ser lida
como uma comparação direta: o escopo do código aumentou com interfaces, fábrica,
estratégias e combos. Os relatórios completos preservam os valores por bloco.

## 5. Prioridades e conclusão

1. **Criar uma rede de segurança:** registrar o comportamento original em testes
   de caracterização antes de refatorar. A evidência atual registra 34/34 casos
   passando tanto no código original quanto no refatorado.
2. **Separar as regras legadas:** aplicar Strategy e Factory para isolar cada
   fórmula e reduzir a complexidade de `ShoppingCart.handle_offers` sem mudar os
   resultados observáveis.
3. **Isolar a nova regra:** manter a promoção de combo em módulo próprio e passar
   ao cálculo apenas as quantidades não consumidas pelas ofertas antigas.
4. **Cobrir requisitos e regressões:** a suíte atual registra 116 testes
   aprovados, incluindo os casos de ofertas antigas, combos, interfaces e
   integração.
5. **Manter explícitos os limites:** o defeito D3 foi preservado; o catálogo
   concreto ainda é um esqueleto de banco; as dependências não estão fixadas por
   versão. Esses pontos não devem ser apresentados como corrigidos.

Na data da análise, a refatoração integrada atende aos testes e reduziu a
complexidade do método central de ofertas. Isso não elimina a necessidade de
manter testes, revisar dependências e implementar a persistência real do catálogo
caso ela faça parte do escopo da aplicação.
