# Plano de Contingência e Refatoração

**Projeto:** Modernização do Supermarket Receipt (AV3, Alta Qualidade de Software, SENAI CIMATEC)
**Responsável pelo documento:** Matheus Sobral
**Repositório:** github.com/Carti-1/Supermarket (branch de integração: `develop`)
**Versão:** 1.1 (25/11/2026)

> Este plano responde a duas perguntas: **se algo der errado, como percebemos?** e **como voltamos a um estado seguro?** Ele vale para todas as mudanças de código da equipe, até o congelamento de 23/11.

---

## 1. Objetivo e escopo

Modernizar o sistema legado de forma **incremental**, sem alterar as regras comerciais já existentes, e acrescentar a promoção de **combos** (10% sobre os itens de combos completos).

Os IDs de requisitos citados (RF01–RF13, RNF01–RNF05) são os do documento de requisitos (`docs/requisitos`, Lucca).

| Dentro do escopo | Fora do escopo |
|---|---|
| Extração das regras de oferta em estratégias (Strategy) | Reescrever o sistema do zero |
| Fábrica de estratégias (Simple Factory) | Mudar valores ou textos das ofertas legadas (exceto o D3, se o grupo decidir) |
| Combos promocionais e integração no `Teller` | Novas dependências em `requirements.txt` só para "gerar resultado" nas auditorias |
| Limpeza de código (`Receipt`, nomes, comentários) | Alterar `tests/test_supermarket.py` |
| Análises Bandit, pip-audit e Safety antes e depois | |

---

## 2. Sequência das mudanças

A ordem foi escolhida para que **toda alteração de código já encontre testes que a protejam**. Primeiro se fixam os contratos e o comportamento atual; só depois se mexe na lógica.

| # | Etapa | Responsável | PR / situação (22/11) | Proteção antes de mudar |
|---|---|---|---|---|
| 1 | Contratos (`src/interfaces.py`) e entidade `Combo` | João | ✅ integrado | `tests/test_interfaces.py` |
| 2 | Testes de caracterização do código original | Heitor | ✅ PR #5 | Execução registrada em `docs/evidencias/` |
| 3 | Limpeza do `Receipt` (Clean Code) | Heitor | ✅ PR #7 | Caracterização + approval do recibo |
| 4 | Contrato `OfferStrategyPort` | Pedro | ✅ PR #8 | `tests/test_interfaces.py` |
| 5 | Estratégias das 4 ofertas legadas | Pedro | ✅ PR #9 | `tests/test_estrategias.py` com os valores da caracterização |
| 6 | Fábrica de estratégias | Matheus | ✅ PR #10 | `tests/test_fabrica_ofertas.py` (stubs) |
| 7 | Carrinho usa a fábrica (remove `if/elif` por tipo) | Pedro | 🔄 branch `feature/carrinho-delega` | Caracterização + `test_supermarket.py` |
| 8 | `ComboPromotion` | Lucca | ✅ PR #13 | `tests/test_combos.py` (cenários com o combo injetado) |
| 9 | `Teller` aplica combos por padrão; remover `xfail` | Matheus | 🔄 PR #14 em revisão | Antes: 4 `XPASS(strict)`; depois: 116 passed, zero `xfail` |
| 10 | Regressão final + cobertura | Heitor | ⏳ 23/11 | Comparação antes/depois |
| 11 | Segurança e métricas "depois" (Bandit, pip-audit, Safety, Radon) | João | ⏳ 23/11 | Linha de base em `docs/seguranca_antes_depois.txt` |
| 12 | Merge `develop` → `main` | Pedro | ⏳ 24/11 | Todos os critérios da seção 9 |

**Congelamento de código: 23/11.** Depois dessa data, só entram correções de defeito (`fix:`) e documentação (`docs:`).

---

## 3. Invariantes de negócio

Regras que **não podem mudar** com a refatoração. Cada uma é verificada por testes já existentes.

| ID | Invariante | Requisito | Verificado por |
|---|---|---|---|
| INV-01 | **3 por 2:** a cada 3 unidades, uma sai de graça; com 2 ou menos não há desconto | RF01–RF04 | `test_comportamento_legado.py`, `test_estrategias.py` |
| INV-02 | **Desconto percentual:** `quantidade × preço × argumento / 100` sobre toda a quantidade | RF01–RF04 | idem |
| INV-03 | **2 por valor fixo:** com menos de 2 unidades não há desconto; mantém a divisão real do legado (ver D3) | RF01–RF04 | idem |
| INV-04 | **5 por valor fixo:** a cada grupo de 5, cobra o valor fixo; o resto paga preço cheio | RF01–RF04 | idem |
| INV-05 | Carrinho sem oferta: total = preço × quantidade, sem descontos | RF05 | testes de caracterização |
| INV-06 | O valor do desconto é sempre registrado como **negativo**, e **total = soma dos itens + soma dos descontos** | RF06 | testes de caracterização |
| INV-07 | Os **textos das descrições** de desconto (ex.: "3 for 2", "… % off", "2 for …", "5 for …") são mantidos como estão hoje | RF06 | testes de caracterização; approval do recibo |
| INV-08 | O **recibo impresso** é idêntico ao aprovado antes da refatoração | RF06 | `tests/test_recibo_impresso.py` + `tests/approved_files/` (Heitor; pendente de integração em 22/11) |
| INV-09 | Um mesmo conjunto de itens **nunca recebe dois descontos** (oferta legada + combo) | RF11 | `tests/test_combos.py` (D1) |

---

## 4. Interfaces públicas congeladas

Estas assinaturas são o **contrato observável** do sistema. Elas não podem mudar nome, parâmetros obrigatórios nem significado do retorno.

| Classe / módulo | Membros congelados |
|---|---|
| `Teller` | `Teller(catalog)`, `add_special_offer(...)`, `checks_out_articles_from(cart)`, `product_with_name(name)` |
| `ShoppingCart` | `add_item`, `add_item_quantity`, `items`, `product_quantities`, `handle_offers` |
| `Receipt` | `total_price`, `add_product`, `add_discount`, `items`, `discounts` |
| `model_objects` | `Product`, `Offer`, `Discount`, `SpecialOfferType` (os 4 valores atuais) |

### 4.1 Mudanças de interface justificadas (compatíveis)

| Mudança | Por que é compatível | Motivo |
|---|---|---|
| `handle_offers` passa a **devolver** as quantidades que sobraram após as ofertas legadas | Antes devolvia `None`; quem ignorava o retorno continua funcionando | O combo usa só as sobras (D1) |
| Catálogo ganha `product_by_name` | Método novo; nada foi removido | `Teller.product_with_name` deixa de depender de atributo interno do `FakeCatalog` (LSP, D4) |
| `Teller` ganha `add_combo_offer` e o parâmetro opcional `combo_promotion` | Parâmetro opcional com valor padrão; `Teller(catalog)` continua válido | Permite injetar um dublê nos testes (DIP) |
| Novo pacote `src/offers/` (estratégias e fábrica) | Interno; não altera nenhuma assinatura pública | SRP, OCP |

Qualquer outra mudança em `src/interfaces.py` vai em **PR próprio**, revisado por todos que dependem do contrato.

---

## 5. Decisões de projeto

| ID | Decisão | Situação |
|---|---|---|
| D1 | **Convivência:** as ofertas legadas são aplicadas primeiro; o combo só usa as unidades que sobraram. Ex.: 4 escovas com "3 por 2" → 3 ficam na oferta legada, 1 pode entrar em combo | ✅ decidida (contrato) |
| D2 | Combo com produto vendido por quilo (quantidade fracionária): permitir, contando apenas combos inteiros (ex.: 1,5 kg exigindo 1,0 kg forma 1 combo) | ✅ decidida (`ComboPromotion`, teste `test_combo_com_produto_por_quilo_conta_combos_inteiros`) |
| D3 | Defeito legado: "2 for 15" com 3 unidades de R$ 10,00 cobra R$ 32,50 (mais que os R$ 30,00 sem oferta). **Mantido de propósito** para preservar o comportamento legado; o combo não o corrige nem o duplica | ✅ decidida (registrada no teste `test_dois_por_valor_reserva_duas_escovas_e_a_terceira_entra_no_combo`) |
| D4 | Busca de produto por nome via `product_by_name` no catálogo | ✅ decidida |
| D6 | Produto usado no `Discount` do combo: um `Product` com o nome do combo, só para rotular a linha (imprime "10% combo (Higiene bucal)") | ✅ decidida (teste `test_recibo_impresso_mostra_a_linha_do_combo`) |
| D7 | Combos sobrepostos: a ordem de cadastro define a prioridade | ✅ decidida |

---

## 6. Riscos

Escala: **B** = baixa, **M** = média, **A** = alta.

| ID | Risco | Prob. | Impacto | Prevenção | Como percebemos | Resposta |
|---|---|---|---|---|---|---|
| R1 | **Regressão de cálculo** em alguma oferta legada | M | A | Caracterização antes de refatorar; estratégias testadas com os mesmos valores | Teste de caracterização ou `test_supermarket.py` falha | Não integrar o PR; se já integrado, `git revert` (seção 7) |
| R2 | **Desconto duplicado** entre oferta legada e combo | M | A | Regra D1: combo só usa as sobras | `test_combos.py` (cenário de convivência) | Corrigir antes do merge |
| R3 | **Combo calculado errado** (incompleto, excedentes, múltiplos combos) | M | A | Testes escritos antes da implementação (`xfail`) | Testes de combo vermelhos | Corrigir na branch do combo |
| R4 | **Erro de import** no pacote novo `src/offers/` | M | M | `__init__.py` no pacote; rodar `pytest` a cada passo | `ModuleNotFoundError` na coleta dos testes | Corrigir na branch antes do PR |
| R5 | **Conflito de merge** entre branches paralelas | A | M | Partir sempre da `develop` atualizada; uma branch por tarefa; PRs pequenos | GitHub indica conflito no PR | Atualizar a branch com a `develop`, resolver localmente, rodar `pytest` |
| R6 | **Arredondamento de float** muda centavos no recibo | M | M | Manter as fórmulas do legado; comparar recibo impresso | Approval test do recibo falha | Ajustar e manter a fórmula original |
| R7 | **Quebra de interface pública** | B | A | Lista de interfaces congeladas (seção 4); revisão obrigatória | `test_supermarket.py` ou `test_interfaces.py` falha | Revert ou ajuste compatível |
| R8 | **Atraso de uma etapa bloqueia outras** (ex.: combo → Teller) | A | M | Contratos definidos antes; testes com stubs | Cronograma da equipe | Avisar o grupo; priorizar o caminho crítico antes do congelamento |
| R9 | **Arquivo commitado por engano** (`.venv/`, `__pycache__/`, logs) | M | B | `.gitignore`; `git add` arquivo por arquivo; `git diff --staged` | Revisão do PR | Remover em commit `chore:` |
| R10 | **Codificação de logs** (UTF-16 no PowerShell 5.1) | M | B | Salvar com `Out-File -Encoding utf8` | Arquivo ilegível no GitHub | Regerar o arquivo |
| R11 | **Commit grande demais para reverter só a parte com defeito** (ex.: o commit inicial de contratos, com 627 linhas em 10 arquivos) | M | M | Commits pequenos, uma intenção cada; código e teste em commits separados | Revisão do PR | Reverter o PR inteiro e reaplicar a parte boa em novo PR |
| R12 | **Dependência nova sem necessidade** (ex.: Radon, Bandit no `requirements.txt`) | B | B | Ferramentas de análise instaladas só localmente; versões registradas nos documentos | `git diff` do `requirements.txt` no PR | Remover em commit `chore:` |

---

## 7. Estratégia de reversão

### 7.1 Antes do merge (PR aberto)
Um PR com testes vermelhos ou comportamento alterado **não é integrado**. A correção é feita na própria branch, com novos commits.

### 7.2 Depois do merge (PR já está na `develop`)
Usamos **`git revert`**, que cria um commit novo que desfaz o merge **sem apagar o histórico**.

```powershell
# 1) Partir da develop atualizada
git switch develop
git pull origin develop

# 2) Encontrar o commit de merge do PR problemático
git log --oneline --merges -10

# 3) Criar uma branch para a reversão
git switch -c revert/pr-<numero>

# 4) Desfazer o merge (-m 1 = manter o lado da develop)
git revert -m 1 <hash-do-merge>

# 5) Confirmar que a suíte voltou ao verde
python -m pytest -q

# 6) Enviar e abrir PR "revert: desfaz PR #<numero>"
git push -u origin revert/pr-<numero>
```

Alternativa equivalente: o botão **Revert** na página do PR integrado, no GitHub, que gera esse mesmo PR de reversão.

### 7.3 O que é proibido
- `git push --force` e `git reset --hard` em `develop` ou `main`: apagam histórico de outros membros.
- Editar `tests/test_supermarket.py` para "fazer o teste passar".

### 7.4 Ponto de restauração
A `main` só recebe a `develop` no fim (24/11), depois de todos os critérios da seção 9. Até lá, ela preserva a versão anterior à refatoração.

---

## 8. Medidas preventivas (rotina de cada mudança)

1. Partir da `develop` atualizada (`git switch develop` → `git pull`) e criar uma branch por tarefa: `feature/…`, `test/…`, `docs/…`, `refactor/…`.
2. Fazer mudanças pequenas e rodar `python -m pytest -q` a cada passo.
3. Adicionar arquivos um a um e conferir com `git diff --staged` antes de cada commit.
4. Usar Conventional Commits em português, uma intenção por commit: `test:`, `refactor:` (não muda comportamento), `feat:` (combo), `fix:` (defeito, commit separado), `docs:`, `chore:`.
5. Integrar só por Pull Request, aprovado por outro membro (de preferência quem consome o contrato alterado).
6. Ninguém edita arquivo de outro membro sem combinar.

---

## 9. Critérios de aceitação

A refatoração é considerada aceita quando **todos** os itens abaixo forem verdadeiros:

| # | Critério | Como verificar |
|---|---|---|
| CA-01 | Todos os testes passam | `python -m pytest -q` sem falhas |
| CA-02 | Nenhum `xfail` restante (combos implementados) | Saída do `pytest` sem `xfailed` |
| CA-03 | `tests/test_supermarket.py` inalterado (RNF01) | `git diff <commit-inicial> -- tests/test_supermarket.py` vazio |
| CA-04 | Recibos aprovados idênticos | Approval tests verdes, sem arquivo `.received` novo |
| CA-05 | Valores das 4 ofertas legadas iguais aos da caracterização | `test_comportamento_legado.py` e `test_estrategias.py` verdes |
| CA-06 | Combos seguem a regra dos 10% em todos os cenários do enunciado (RF07–RF12) | `test_combos.py`: completo, incompleto, múltiplos, excedentes, convivência |
| CA-07 | Nenhum alerta de segurança novo sem justificativa (RNF05) | Comparação Bandit / pip-audit / Safety antes e depois |
| CA-08 | Todo código integrado passou por PR revisado | Histórico de PRs no GitHub |
| CA-09 | Nova promoção entrou sem editar o carrinho (OCP) | `git log -- src/shopping_cart.py` sem commits do combo (RNF02) |
| CA-10 | `requirements.txt` sem dependências novas | `git diff` do arquivo vazio em relação ao original (RNF04) |

---

## 10. Rastreabilidade

| Mudança | Arquivo(s) | Testes associados | Evidência |
|---|---|---|---|
| Caracterização | `tests/test_comportamento_legado.py` | o próprio arquivo | `docs/evidencias/caracterizacao_*.txt` |
| Strategy (ofertas) | `src/offers/legacy_strategies.py` | `tests/test_estrategias.py`, `tests/test_ofertas_legadas.py` | PR #9 |
| Factory | `src/offers/offer_factory.py` | `tests/test_fabrica_ofertas.py` | PR #10 |
| Combos | `src/offers/combo_promotion.py`, `src/teller.py` | `tests/test_combos.py` | PR do combo e do Teller |
| Segurança | — | — | `docs/seguranca_antes_depois.txt` |

---

## Histórico do documento

| Data | Versão | Autor | Alteração |
|---|---|---|---|
| 22/11/2026 | 1.0 | Matheus Sobral | Versão inicial, alinhada aos guias da equipe e ao estado da `develop` em 22/11 |
| 25/11/2026 | 1.1 | Matheus Sobral | Situação das etapas atualizada (PRs #10, #13 e #14); decisões D2, D3 e D6 registradas como fechadas |
