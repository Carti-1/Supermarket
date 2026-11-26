# Diagnóstico técnico do legado

- **Projeto:** Modernização do Supermarket Receipt (AV3)
- **Data:** 25/11/2026
- **Código original:** `ff9b330` (`origin/main`)
- **Código atual analisado:** `5b73a5e` (`develop`, integração até o PR #18)
- **Responsável:** João

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

| Arquivo e linha original | Exemplo original | Problema e efeito | Situação após a refatoração |
|---|---|---|---|
| `shopping_cart.py:30-68` | `def handle_offers(self, receipt, offers, catalog):` seguido por vários `if offer.offer_type == ...` | Um método concentra a seleção e o cálculo de todas as ofertas. A complexidade C (13) aumenta o número de caminhos a entender e testar; cada nova oferta exigia alterar o carrinho, contrariando OCP. | O carrinho delega o cálculo às estratégias obtidas por `OfferStrategyFactory`. `handle_offers` caiu para A (4), e a lógica de combos está em `src/offers/combo_promotion.py`. A fábrica e as estratégias têm testes isolados. |
| `shopping_cart.py:6-28` e `30-68` | `ShoppingCart` guarda `_items` e `_product_quantities` e também calcula descontos em `handle_offers`. | A classe tem motivos distintos para mudar: armazenamento do carrinho e regras promocionais, contrariando SRP. | O carrinho ainda mantém os itens e coordena a aplicação das ofertas antigas, mas cada regra antiga fica em uma estratégia. O cálculo do combo também está separado. |
| `shopping_cart.py:31, 38-52, 55, 64` | `for p ...`, `x = 1`, `x = 3`, `x = 2`, `x = 5` e `number_of_x` | Nomes curtos e valores numéricos espalhados tornam a regra mais lenta de ler e podem ocultar a intenção. | As regras foram distribuídas em classes nomeadas (`ThreeForTwoStrategy`, `TwoForAmountStrategy`, etc.) e usam nomes mais explicativos como `groups` e `charged`. Os tamanhos de grupo 2, 3 e 5 continuam como valores numéricos locais à estratégia; extraí-los para constantes nomeadas é uma melhoria possível, não requisito para a correção funcional. |
| `shopping_cart.py:45` | `offer.argument * (quantity_as_int / x)` | A divisão real na promoção “2 por X” produz o defeito D3: 3 unidades a R$ 10,00 com “2 por 15” resultam em R$ 32,50. | A fórmula foi preservada em `TwoForAmountStrategy` e é coberta por teste de caracterização. A equipe documentou a decisão; uma correção comercial exigiria decisão do grupo e alteração separada. |
| `shopping_cart.py:45-65` | Cálculos distintos para “2 por X” e “5 por X” dentro do mesmo método. | Regras de promoções diferentes estão misturadas e são difíceis de testar isoladamente; uma alteração pode afetar outra oferta. | Cada promoção legada tem estratégia própria. A similaridade visual não justificou unificar regras com resultados diferentes, especialmente por causa do D3. |
| `teller.py:28-29` | `return self.catalog.products.get(name, None)` | O caixa depende de um atributo interno que existia no catálogo falso usado pelos testes, e não fazia parte do contrato comum: fragilidade de substituição (LSP). | `Teller.product_with_name` agora chama `CatalogReaderPort.product_by_name`. O catálogo declara a operação e o teste cobre produto encontrado e ausente. |
| `catalog.py:4-8` | `raise Exception("cannot be called from a unit test - it accesses the database")` | A implementação de catálogo do kata é um esqueleto que lança exceções genéricas; seu contrato e implementação de persistência não estão concluídos. Isso limita testes de integração com banco. | As interfaces `CatalogReaderPort` e `CatalogWriterPort` tornam explícitas as operações esperadas. `SupermarketCatalog` continua sendo um placeholder sem banco; os testes usam `FakeCatalog`, sem alegar que a persistência real foi implementada. |
| `tests/test_supermarket.py` | A suíte original continha um teste. | Um único caso não protegia suficientemente as ofertas, o recibo nem a nova regra contra regressões. | A suíte integrada atual tem 116 testes aprovados. A equipe também compara os 34 testes de caracterização no original e no refatorado. |
| `requirements.txt` | Dependências sem versões fixadas. | Uma instalação futura pode resolver versões diferentes, reduzindo a reprodutibilidade do ambiente. | A lista foi mantida sem novas dependências de aplicação. O pinning continua sendo uma decisão documental/operacional pendente; Radon foi instalado apenas no ambiente virtual local para esta medição, não foi adicionado a `requirements.txt`. |

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
