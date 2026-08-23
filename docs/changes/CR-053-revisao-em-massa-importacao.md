# Change Request — CR-053: Revisão em Massa da Importação de Extratos (F07)

**Versão:** 1.0
**Data:** 2026-08-22
**Status:** Em Implementação
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

A revisão de uma importação é feita linha a linha: uma fatura de cartão traz 40–80 transações e cada uma exige até três seleções (categoria, subcategoria, método). Não há busca, não há edição em lote e não há nenhum somatório na tela para conferir o total extraído contra o valor do documento.

Este CR entrega a **frente "revisão em massa"** do item **E-C** do [roadmap de evolução da F07 (v2)](../F07-v2-roadmap-importacao.md), que ataca a lacuna **L2 — revisão trabalhosa**: busca por texto, filtro por grupo, aplicação de categoria/subcategoria/método/ação em lote, e totais por grupo, por alvo e por lote.

A outra frente da E-C — **memória de categorização** (tabela `import_category_rules`, aprendizado no confirm, few-shot no prompt) — fica para o **CR-054** e não é tocada aqui.

**Escopo:** frontend puro. Nenhum endpoint novo, nenhuma migration, nenhuma mudança no payload do confirm.

---

## 2. Classificação

| Campo            | Valor                                              |
|------------------|----------------------------------------------------|
| Tipo             | Nova Feature (+ Refactoring preparatório)          |
| Origem           | Evolução do produto (roadmap F07 v2, E-C)          |
| Urgência         | Próxima sprint                                     |
| Complexidade     | Média (frontend; refactor de componente + helpers puros) |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

`ImportReview.tsx` renderiza as transações em cinco grupos fixos (novos gastos / conciliações / compras parceladas / ignoradas / duplicadas), cada linha com seus editores inline. Não existe:

- nenhuma forma de buscar ou filtrar as linhas;
- nenhuma forma de aplicar um valor a várias linhas de uma vez;
- nenhum somatório — nem por grupo, nem do lote.

O cabeçalho mostra apenas `"{n} de {N} transações selecionadas"`, sem valor.

Estruturalmente, o arquivo tem **441 linhas**, das quais **255 são uma função `renderRow` declarada dentro do componente** — recriada a cada render, sem `React.memo` em lugar nenhum. Digitar um caractere em qualquer campo re-renderiza todas as linhas da tela, cada uma com dois a três `<select>` populados a partir do mapa de categorias.

### Problema ou Necessidade

Categorizar oito corridas de Uber numa fatura custa hoje 24 interações (8 × categoria + subcategoria + método). E, sem somatório, não há como o usuário verificar se a IA extraiu a fatura inteira — o único detector de extração incompleta é ele perceber a falta de um lançamento.

### Situação Desejada (TO-BE)

O usuário digita "uber" na busca, sobram 8 linhas, escolhe categoria + subcategoria + método uma vez e aplica às 8 — 4 interações. Os subtotais por grupo e o total do lote ficam visíveis o tempo todo, permitindo bater a soma contra o valor da fatura de olho enquanto a reconciliação automática (item E-D) não existe.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| # | Item | Antes (AS-IS) | Depois (TO-BE) |
|---|------|---------------|----------------|
| 1 | Busca | Inexistente | Campo de busca casando a descrição da IA **ou** a editada, insensível a caixa e acento |
| 2 | Filtro por grupo | Inexistente | Chips para isolar um ou mais dos cinco grupos |
| 3 | Edição em lote | Inexistente | Barra de ações aplicando categoria, subcategoria, método e "tratar como novo gasto diário" às linhas visíveis e incluídas |
| 4 | Inclusão em lote | Checkbox linha a linha | + "Marcar todas as visíveis" / "Desmarcar todas as visíveis" |
| 5 | Totais | Nenhum | Subtotal por grupo, total do alvo do bulk, e total do lote no cabeçalho |
| 6 | Contagem por grupo | `Novos gastos diários (47)` | `Novos gastos diários (8 de 47)` quando há filtro ativo |
| 7 | Grupo vazio sob filtro | Some da tela | Continua visível com "0 de N" e mensagem "nenhuma linha corresponde ao filtro" |
| 8 | Valor no cabeçalho da linha | `tx.valor` (o da IA), divergindo do input editado logo abaixo | Valor efetivo da linha, batendo com os subtotais |
| 9 | Erro de confirm com linha oculta | "Corrija os campos destacados" sem campo destacado visível | O filtro é limpo automaticamente e a linha com erro reaparece |
| 10 | Estrutura do componente | 1 arquivo de 441 linhas, `renderRow` inline sem memo | 4 arquivos; linha memoizada com `React.memo` + `updateDecision` em `useCallback` |

### 4.2 O que NÃO muda

- **Contrato com o backend.** `buildConfirmPayload` fica intocado; o payload do `POST /api/imports/{id}/confirm` é byte-a-byte o mesmo. Nenhum endpoint novo, nenhuma mudança de schema.
- **Semântica do checkbox da linha:** continua significando "incluir esta transação na importação" (RN-038 — staging obrigatório).
- **`buildInitialDecisions`:** ignoradas e duplicadas continuam nascendo desmarcadas.
- **Validação por linha** (`validateDecision`) e a guarda de "um planejado só é pago uma vez por lote".
- **Agrupamento** (`groupTransactions`) e a precedência `duplicada` > classificação.
- **Invariante do `ImportView`:** ao entrar na revisão o lote é copiado para o state e o polling desligado (CR-052).
- Toda a frente de **memória de categorização** da E-C — vai para o CR-054.

### 4.3 Decisões de desenho

| Decisão | Justificativa |
|---------|---------------|
| **O filtro é a seleção.** Sem checkbox de seleção separada; o bulk opera sobre "as N linhas visíveis e incluídas" | O checkbox da linha já significa "incluir". Um segundo checkbox criaria dois eixos concorrentes em telas de até 80 linhas, e um "selecionar todas" varreria ignoradas/duplicadas que nascem desmarcadas de propósito |
| **Split do componente antes de somar features**, em commit próprio sem mudança funcional | Somar filtro + barra + totais a um arquivo de 441 linhas o levaria a ~650 e agravaria a re-renderização por tecla. O split isolado mantém o diff da revisão legível |
| **Bulk de `acao` limitado a `criar_gasto_diario`** | `atualizar_planejado` exige `expenseId` por linha e `criar_planejado_parcelado` exige numeração por linha — aplicar em lote produziria N linhas que não validam. `criar_gasto_diario` é a única direção auto-suficiente, e cobre o caso real (resgatar linha que a IA marcou como `ignorar`, rebaixar parcelamento falso) |
| **Toda lógica nova é função pura em `utils/importReview.ts`** | O repo não tem `@testing-library/react` e zero testes de componente. Adicionar RTL seria dependência nova disparando o checklist de auditoria — desproporcional aqui. Registrado como follow-up |
| **Valor efetivo = editado quando finito e > 0, senão o da IA** | Input vazio ou meio-digitado é estado transitório, não zero — tratá-lo como zero faria o total piscar durante a digitação |
| **Nenhuma RN nova, nenhum ADR novo** | É afordância de UI, não regra de negócio nem decisão de arquitetura; o contrato com o backend não muda |

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|-----------|-----------------|-----------------|
| `/docs/01-PRD.md` | Sim | RF-21 (detalhamento), histórico de versões | Bullet no detalhamento do RF-21 + versão v3.4. **Sem RN nova** — é UI, não regra de negócio |
| `/docs/02-ARCHITECTURE.md` | Não | — | Sem ADR novo: nenhuma decisão de arquitetura, contrato inalterado |
| `/docs/03-SPEC.md` | Não | — | É índice; a spec detalhada é a 10 |
| `/docs/specs/10-importacao-extratos.md` | Sim | Título, Frontend, Referências | Bullets do `ImportReview` e dos helpers novos |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | CR Ref, Visão Geral | Uma linha na tabela |
| `/docs/05-DEPLOY-GUIDE.md` | Não | — | Sem migration, sem variável de ambiente nova |
| `/docs/F07-v2-roadmap-importacao.md` | Sim | §4 E-C, §6 Rastreabilidade, Changelog | E-C marcada **parcialmente**: frente revisão ✅ CR-053, frente memória aberta |
| `/docs/changes/INDEX.md` | Sim | Lista | Entrada do CR-053 + rotação do CR-048 vindo do CLAUDE.md |
| `CLAUDE.md` | Sim | Change Requests | Lista dos 5 mais recentes |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição da Mudança |
|------|---------|----------------------|
| Criar | `frontend/src/components/imports/fieldStyles.ts` | `inputClass` extraído (hoje privado no `ImportReview`) |
| Criar | `frontend/src/components/imports/ImportReviewRow.tsx` | A linha + editores inline, em `React.memo` |
| Criar | `frontend/src/components/imports/ImportReviewGroup.tsx` | Cabeçalho do grupo (título, "X de N", subtotal) + lista |
| Criar | `frontend/src/components/imports/ImportReviewToolbar.tsx` | Busca, chips de grupo, barra de ações em lote, totais |
| Modificar | `frontend/src/components/imports/ImportReview.tsx` | Reduzido a estado + layout; `updateDecision` em `useCallback`; `handleBulkApply` |
| Modificar | `frontend/src/utils/importReview.ts` | + helpers puros de filtro, totais e bulk |
| Modificar | `frontend/src/utils/importReview.test.ts` | + suítes dos helpers novos |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| — | Nenhuma alteração de schema | **Não** |

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|-----------|-----------|
| CR-T-01 | Extrair `fieldStyles.ts` e `ImportReviewRow.tsx` memoizada; `updateDecision` em `useCallback` | — | tsc + lint limpos; tela idêntica |
| CR-T-02 | Extrair `ImportReviewGroup.tsx` | CR-T-01 | idem |
| CR-T-03 | `ImportReview.tsx` reduzido a estado + layout | CR-T-02 | Commit de refactor fecha sem mudança funcional |
| CR-T-04 | Helpers de filtro (`normalizeForSearch`, `matchesFilter`, `filterGroups`) | — | Funções puras, sem import de React |
| CR-T-05 | Helpers de totais (`decisionValor`, `sumTransactions`) | — | idem |
| CR-T-06 | Helpers de bulk (`bulkTargetIds`, `applyBulkPatch`) | CR-T-04 | Cascata categoria→subcategoria honrada; não muta o input |
| CR-T-07 | `ImportReviewToolbar.tsx` — busca, chips, barra de ações, totais | CR-T-03..06 | Barra informa o número exato de linhas afetadas |
| CR-T-08 | Ligar no `ImportReview`: "X de N", subtotais, total do lote, limpar filtro no erro de confirm | CR-T-07 | Fluxo completo funcionando |
| CR-T-09 | Testes Vitest dos helpers novos | CR-T-04..06 | Suíte verde |
| CR-T-10 | Revisão de segurança | CR-T-08 | Registrada em §13 |
| CR-T-11 | Validação runtime via Playwright (CR-037) | CR-T-09 | Registrada em §11 |
| CR-T-12 | `/code-review` no diff da branch (CR-040) | CR-T-11 | Findings corrigidos ou justificados em §12 |
| CR-T-13 | Atualizar documentação | CR-T-12 | Docs de §5 atualizados |

---

## 8. Critérios de Aceite

- [x] Busca por texto filtra as linhas casando a descrição da IA ou a editada, insensível a caixa e acento — §11 cenários 3–5
- [x] Chips isolam um ou mais grupos; combinam com a busca — §11 cenário 7
- [x] Aplicar categoria + subcategoria + método em lote altera exatamente as linhas visíveis e incluídas, e nenhuma outra — §11 cenário 8
- [x] Bulk "tratar como novo gasto diário" muda a ação das linhas alvo — §11 cenário 12
- [x] "Marcar/desmarcar todas as visíveis" opera só sobre o conjunto visível **e nunca sobre duplicadas** — §11 cenários 9 e 15
- [x] Subtotal por grupo, total do alvo e total do lote corretos e batendo entre si — §11 cenários 2 e 14 (os cinco subtotais somam R$ 2.671,26 = total do cabeçalho)
- [x] Linha escondida pelo filtro preserva sua decisão e continua indo no payload do confirm — §11 cenário 10 + teste unitário dedicado
- [x] Confirm com erro em linha oculta limpa o filtro e destaca a linha — §11 cenário 11
- [x] Payload do confirm inalterado em relação ao CR-049/CR-052 — `buildConfirmPayload` não foi tocado; §11 cenário 13 gravou as 4 ações corretamente
- [x] Testes existentes continuam passando (regressão) — 202 backend, 120 Vitest (baseline 70)
- [x] Novos testes cobrem a mudança — 50 Vitest novos (44 dos helpers + 6 de regressão dos findings)
- [x] Fluxo afetado exercitado em runtime antes do merge (CR-037) — ver §11
- [x] Revisão de código pré-merge (CR-040) — ver §12
- [x] Revisão de segurança — ver §13
- [x] Documentos afetados foram atualizados — spec 10, roadmap F07, PRD v3.4, Implementation Plan, CLAUDE.md, INDEX
- [ ] CI verde após o push (`gh run watch`)

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. Critério pendente de evento posterior (ex: CI verde após push) mantém o CR "Em Implementação" até o follow-up.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Filtro esconde linha com erro de validação e o usuário não entende por que o confirm não passa | Alta | Médio | O filtro é limpo automaticamente quando o confirm falha com erros (item 9 de §4.1) |
| 2 | Filtrar remove a linha do payload do confirm | Baixa | Alto | `filterGroups` filtra **só a lista de render**; `decisions` nunca é tocado. Teste unitário dedicado + passo 8 da validação runtime |
| 3 | Bulk sobrescreve categoria já correta de uma linha que o usuário não queria mudar | Média | Baixo | A barra informa o número exato de linhas antes de aplicar; nada é persistido até o confirm; a linha continua editável |
| 4 | O split do componente regride a tela | Média | Alto | Commit separado, sem mudança funcional; validação runtime do fluxo antes de somar features |
| 5 | `React.memo` não memoiza nada por callback instável | Média | Baixo | `updateDecision` em `useCallback` com deps vazias; conferido no React DevTools durante a validação |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código

- **Método:** `git checkout -b hotfix/revert-CR-053` → `git revert -m 1 [hash do merge]` → merge em `master` → push
- **Método alternativo:** redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** o merge commit da branch `feat/CR-053-revisao-em-massa-importacao`

### 10.2 Rollback de Migration

- **N/A** — o CR não tem migration.

### 10.3 Impacto em Dados

- **Dados serão perdidos no rollback?** Não. O CR não persiste nada de novo; toda a mudança vive no estado local da tela de revisão.
- **Backup necessário antes do deploy?** Não.

### 10.4 Rollback de Variáveis de Ambiente

- **Variáveis novas/alteradas:** Nenhuma.

### 10.5 Verificação Pós-Rollback

- [ ] Aplicação acessível e funcional
- [ ] Fluxo de importação completo (upload → processing → revisão → confirm) funcionando na forma do CR-052
- [ ] Usuários existentes conseguem fazer login

---

## 11. Validação Runtime (CR-037)

**Ambiente.** SQLite local isolado — `DATABASE_URL="sqlite:///./local_cr053.db"` em todos os comandos. Conferido antes de qualquer escrita: sem o override, `engine.url` aponta para `switchyard.proxy.rlwy.net/railway`, ou seja, o **PostgreSQL de produção** (o mesmo tropeço registrado no CR-049). Backend `uvicorn` + frontend `npm run dev`, exercitado via Playwright MCP.

**Massa.** Não há `ANTHROPIC_API_KEY` local e este CR **não toca o caminho da IA**, então o lote foi semeado direto em staging (script no scratchpad da sessão, não commitado — o diff do CR é só `frontend/` + `docs/`): 1 lote `pendente_revisao` com **50 transações** cobrindo os cinco grupos — 30 gastos diários (12 deles variantes de "UBER *TRIP", 15 sem categoria), 3 conciliações apontando para `Expense` reais, 4 parcelamentos numerados, 8 ignoradas, 5 duplicadas. Volume importa: o CR só tem valor a 40–80 linhas.

| # | Exercitado | Resultado |
|---|-----------|-----------|
| 1 | Revisão abre com os 5 grupos | 30 + 3 + 4 + 8 + 5 = 50 ✅ |
| 2 | Subtotais por grupo × total do cabeçalho | 1.728,32 + 402,34 + 540,60 + 0 + 0 = **R$ 2.671,26** = cabeçalho ✅ |
| 3 | Busca "uber" | 14 visíveis (12 novos + 1 ignorada + 1 duplicada); alvo do bulk = 12 ✅ |
| 4 | Busca ativa × total do lote | Cabeçalho e rodapé **inalterados** — filtro é só visão ✅ |
| 5 | Busca "alimentacao" e "ALIMENTAÇÃO" | Ambas casam "PANIFICADORA ALIMENTAÇÃO" ✅ |
| 6 | Busca "zzzz" | Estado vazio único + "Limpar filtro" ✅ |
| 7 | Chip "Ignoradas" | Isola o grupo; demais com "(0 de N)" e mensagem muda ✅ |
| 8 | Categoria + subcategoria + método em lote nas 12 UBER | As 12 receberam Transporte / Uber-99-Taxi / Pix; **IFOOD, PADARIA e NETFLIX (fora do filtro) intactas**; selects da barra voltaram ao placeholder ✅ |
| 9 | "Marcar as 8 visíveis" sobre Ignoradas | 37 → 45 incluídas; total +R$ 11.395,25, exatamente o subtotal do grupo ✅ |
| 10 | Filtrar após editar, depois limpar o filtro | Decisões das linhas ocultas preservadas ✅ |
| 11 | Confirmar com linha inválida **oculta pelo filtro** | Filtro se limpou sozinho (busca e chips zerados) e os 23 erros apareceram nas linhas certas ✅ |
| 12 | "Tratar como novo gasto diário" | Ação trocada nas linhas alvo ✅ |
| 13 | Confirmar de verdade | "30 gastos diários · 25 parcelas · 3 planejados pagos · 8 descartadas". Banco: 12 `DailyExpense` com Transporte/Pix e 18 com Alimentação (as duas aplicações em lote), 28 `Expense` (3 + 25 parcelas) com 7 Pago (3 conciliados + 4 âncoras), lote `confirmado`, transações 37 confirmada / 8 descartada / 5 duplicada ✅ |

**Revalidação após os findings do §12** — os quatro tocam comportamento visível, então o ambiente foi reconstruído e reexercitado:

| # | Exercitado | Resultado |
|---|-----------|-----------|
| 14 | Subtotais somam o cabeçalho (finding 2) | Ignoradas e Duplicadas agora R$ 0,00; soma = R$ 2.671,26 = cabeçalho ✅ |
| 15 | "Marcar as N visíveis" (finding 3) | **45**, não 50 — as 5 duplicadas ficaram de fora ✅ |
| 16 | Categoria sem subcategoria (finding 4) | "Aplicar" desabilitado + aviso; par completo habilita ✅ |
| 17 | Editar valor 14,50 → 500 (finding 1) | Linha passa a R$ 500,00 e o subtotal sobe R$ 485,50 (exato); limpar o campo volta a R$ 14,50 sem piscar zero ✅ |

**Console do browser:** 0 erros da aplicação. As entradas presentes são ruído do dev server (WebSocket de HMR do Vite) e dois `401` em `/api/auth/refresh` das navegações diretas anteriores ao login — comportamento esperado do interceptor.

**Endpoints tocados na sessão:** apenas os já existentes (`/api/imports/pending`, `/api/imports/{id}`, `/api/imports/{id}/confirm`, `/api/months/...`, `/api/daily-expenses/categories`). Nenhum endpoint novo — evidência do "zero backend".

**Encerramento:** servidores derrubados, `local_cr053.db` removido, `git status` limpo (só o `backend/scripts/list_users.py` pré-existente, que não pertence a este CR).

---

## 12. Revisão de Código Pré-Merge (CR-040)

`/code-review high` sobre `git diff master...HEAD` (5 commits, 1411 inserções). **4 findings; 4 corrigidos, 0 justificados.**

| # | Finding | Tratamento |
|---|---------|-----------|
| 1 | Cabeçalho da linha renderizava `formatBRL(tx.valor)` (valor da IA) enquanto os subtotais usavam o editado: editar 50 → 500 movia o subtotal e a linha seguia lendo R$ 50,00 | **Corrigido** — passa a usar `decisionValor`. Era promessa do próprio CR (§4.1 item 8) que ficou para trás na implementação |
| 2 | Subtotal do grupo somava todas as linhas enquanto o total do cabeçalho contava só as incluídas: os cinco subtotais nunca fechavam com o total, e Ignoradas/Duplicadas exibiam em negrito dinheiro que não seria importado | **Corrigido** — subtotal passa a usar `onlyIncluded: true` |
| 3 | "Marcar as N visíveis" sem filtro varria o lote inteiro, **inclusive duplicadas** — que costumam vir com categoria/método completos da importação anterior, logo passariam na validação e seriam regravadas, dobrando o lançamento. Exatamente a varredura que o §4.3 dizia estar evitando | **Corrigido** — `bulkIncludeTargetIds` exclui duplicadas; o resgate delas continua linha a linha, onde o usuário vê o aviso "já importada anteriormente" |
| 4 | Aplicar categoria sem subcategoria zerava a subcategoria de todo o alvo, invalidando parcelados que eram válidos com as duas vazias — erro só aparecendo no Confirmar | **Corrigido** — a toolbar exige o par completo (categoria sozinha nunca é válida em nenhuma ação) e exibe o motivo |

Após as correções: **202 backend + 120 Vitest verdes**, `tsc --noEmit` limpo, `eslint` 0 erros. Os quatro ganharam cobertura: 6 testes unitários novos (findings 3 e 4, lógica pura) e os cenários 14–17 do §11 (findings 1 e 2, render).

O revisor confirmou também os invariantes centrais do desenho: `filterGroups` filtra de fato só a lista de render (`decisions` e o payload intactos), `updateDecision` é `useCallback` estável — então o `memo` da linha vale —, o caminho de erro oculto/limpa-filtro está correto, e `applyBulkPatch` não muta.

> **Follow-up registrado, fora do escopo deste CR:** adotar `@testing-library/react` para cobrir a fiação de componente, hoje verificável só em runtime (ver §13).

---

## 13. Revisão de Segurança (OWASP)

O CLAUDE.md permite pular com justificativa quando o CR é exclusivamente mudança de UI sem endpoints novos, que é o caso. Ainda assim, os itens que poderiam esconder surpresa foram verificados de fato:

| Item | Resultado |
|------|-----------|
| Segredos hardcoded | N/A — nenhum segredo no diff (só componentes e helpers puros) |
| Inputs validados via Pydantic | **Inalterado** — o payload do confirm é byte-a-byte o mesmo; toda a validação do backend (`imports.py`, par categoria/subcategoria, ownership) segue valendo. A validação nova é de UI, em cima da já existente |
| Tokens sensíveis fora do `localStorage` | N/A — o CR não toca auth |
| Ownership | **Inalterado** — nenhum endpoint novo; o confirm continua verificando dono do lote e dos `Expense` |
| Queries ORM parametrizadas | N/A — zero backend |
| CORS / headers de segurança | N/A |
| **Nova dependência** | **Nenhuma.** `package.json` não mudou no diff — a decisão de não adotar RTL neste CR é o que mantém este item limpo, e está registrada, não omitida |
| Rate limit | Inalterado (5/min no upload) |

**Superfície nova considerada.** A busca é o único ponto que lê texto livre do usuário. O texto é usado apenas em comparação de string dentro de `matchesFilter` — nunca em query, nunca em URL — e o estado vazio **não ecoa o termo digitado** de volta na tela. Não há `dangerouslySetInnerHTML` em nenhum arquivo do diff (conferido por grep). React escapa por padrão.

**Lacuna de cobertura declarada.** O repositório não tem `@testing-library/react` e zero testes de componente; adicioná-lo seriam 3 dependências novas + `setupFiles`, disparando auditoria — desproporcional para um CR de UI. Consequência assumida: a fiação dos componentes (toolbar → estado, memoização, render dos grupos, reset dos selects) não tem teste unitário e é coberta apenas pela validação runtime do §11. Registrado como follow-up.

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-22 | Claude | CR criado a partir do item E-C do roadmap F07 v2, restrito à frente "revisão em massa" |
| 2026-08-22 | Claude | Refactor do ImportReview em Row/Group/Toolbar (441 para 174 linhas), sem mudança funcional |
| 2026-08-22 | Claude | Helpers puros de filtro, totais e edição em massa + 44 testes Vitest |
| 2026-08-22 | Claude | Toolbar, contadores "X de N", subtotais e limpeza de filtro no erro de confirm |
| 2026-08-22 | Claude | Validação runtime via Playwright — 13 cenários (§11) |
| 2026-08-22 | Claude | Code review: 4 findings, 4 corrigidos + 6 testes de regressão; revalidação runtime (cenários 14–17) |
| 2026-08-22 | Claude | Revisão de segurança (§13) e documentação sincronizada |
