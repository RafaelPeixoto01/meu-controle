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

- [ ] Busca por texto filtra as linhas casando a descrição da IA ou a editada, insensível a caixa e acento
- [ ] Chips isolam um ou mais grupos; combinam com a busca
- [ ] Aplicar categoria + subcategoria + método em lote altera exatamente as linhas visíveis e incluídas, e nenhuma outra
- [ ] Bulk "tratar como novo gasto diário" muda a ação das linhas alvo
- [ ] "Marcar/desmarcar todas as visíveis" opera só sobre o conjunto visível
- [ ] Subtotal por grupo, total do alvo e total do lote corretos e batendo entre si
- [ ] Linha escondida pelo filtro preserva sua decisão e continua indo no payload do confirm
- [ ] Confirm com erro em linha oculta limpa o filtro e destaca a linha
- [ ] Payload do confirm inalterado em relação ao CR-049/CR-052
- [ ] Testes existentes continuam passando (regressão) — baseline: 202 backend, 70 Vitest
- [ ] Novos testes cobrem a mudança
- [ ] Fluxo afetado exercitado em runtime antes do merge (CR-037) — ver §11
- [ ] Revisão de código pré-merge (CR-040) — ver §12
- [ ] Revisão de segurança — ver §13
- [ ] Documentos afetados foram atualizados
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

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-22 | Claude | CR criado a partir do item E-C do roadmap F07 v2, restrito à frente "revisão em massa" |
