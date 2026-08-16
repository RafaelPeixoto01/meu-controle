# Change Request — CR-049: Importação de Compras Parceladas (F07 — E-A)

**Versão:** 1.0
**Data:** 2026-08-16
**Status:** Em Implementação
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Implementar a evolução **E-A** do [roadmap da F07 v2](../F07-v2-roadmap-importacao.md): reconhecer compras parceladas em faturas de cartão e transformá-las em **gastos planejados com todas as parcelas**, em vez de um gasto diário isolado.

Uma linha como `NETSHOES PARC 03/10` hoje vira um único `DailyExpense` de R$ X, perdendo as 7 parcelas futuras — justamente o dado que alimenta a projeção de parcelas (CR-021) e o fator D2 do health score. Após este CR, ela passa a gerar a parcela 3/10 (já **Paga**, pois a compra apareceu na fatura) mais as parcelas 4..10 como Pendentes.

Entrega **backend + frontend no mesmo CR** (decisão do autor; a F07 original foi dividida em dois por ser um módulo inteiro, não uma extensão dele).

---

## 2. Classificação

| Campo            | Valor                          |
|------------------|--------------------------------|
| Tipo             | Nova Feature                   |
| Origem           | Evolução do produto (roadmap F07 v2, item E-A) |
| Urgência         | Próxima sprint                 |
| Complexidade     | Alta                           |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

`CLASSIFICACOES_VALIDAS` em [`import_service.py:33`](../../backend/app/import_service.py#L33) conhece apenas `gasto_diario | match_planejado | ignorar`. Uma compra parcelada na fatura só é reconhecida se **já existir** um gasto planejado correspondente na lista de candidatos a conciliação — caso contrário cai em `gasto_diario`.

O modelo de dados já suporta parcelamento (`Expense.parcela_atual` / `parcela_total`) e o [router de expenses](../../backend/app/routers/expenses.py#L119-L149) já cria todas as parcelas futuras *upfront* ao cadastrar uma despesa parcelada manualmente. A importação simplesmente não sabe produzir esse formato.

### Problema ou Necessidade

Quem parcela compras no cartão precisa cadastrar cada parcelamento à mão depois de importar a fatura, ou perde a visão de comprometimento futuro — que é exatamente o que a projeção de parcelas e o health score consomem.

### Situação Desejada (TO-BE)

A IA classifica a linha como `parcelamento` e devolve `parcela_atual`/`parcela_total`. Na revisão, a transação aparece num grupo próprio ("Compras parceladas") mostrando o que será criado. Ao confirmar, o sistema cria a série completa de parcelas a partir da atual.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|---------------|----------------|
| 1  | Classificações da IA | `gasto_diario \| match_planejado \| ignorar` | + `parcelamento` |
| 2  | Compra parcelada sem planejado existente | Vira um `DailyExpense` isolado | Vira série de `Expense` com `parcela_atual`/`parcela_total` |
| 3  | Ações do confirm | `criar_gasto_diario \| atualizar_planejado \| descartar` | + `criar_planejado_parcelado` |
| 4  | Criação de parcelas upfront | Lógica inline no router de expenses | Extraída para `services.create_expense_with_installments()`, usada pelos dois caminhos |
| 5  | Staging | Sem campos de parcela | `import_transactions.parcela_atual` / `parcela_total` + auditoria `expense_id_criado` (migration 010) |
| 6  | Resultado da importação | 3 contadores | + `planejados_criados` |

**Regras decididas (autor, 2026-08-16):**

- **RN-044 (nova):** a parcela correspondente à transação importada nasce com status **Pago** (a compra já foi cobrada na fatura); as parcelas seguintes nascem **Pendente**.
- **RN-045 (nova):** o vencimento de cada parcela é a **data da compra + N meses**, via `add_months` (que já preserva o dia e trata meses curtos). Não depende de a IA extrair a data de vencimento da fatura.
- **RN-046 (nova):** parcela que já existe no mês-alvo (mesmo nome + `parcela_atual` + `parcela_total`) não é recriada — importar a fatura do mês seguinte concilia em vez de duplicar.

### 4.2 O que NÃO muda

- **Receitas continuam em `ignorar`** — RN-041 inalterada (fora do escopo do roadmap por decisão do autor)
- As três classificações existentes e suas ações de confirm
- Dedup por fingerprint (RN-042), staging obrigatório (RN-038), PDF nunca persistido (RN-043)
- Upload síncrono, rate limit, feature flag e tratamento de indisponibilidade/erro
- CRUD manual de gastos planejados e diários — inclusive o comportamento atual do `POST /api/expenses/{year}/{month}`, que só muda de *lugar* no código (refactor), não de comportamento
- Tabelas `expenses` / `daily_expenses` — nenhuma coluna nova

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Sim | RF-21 (F07), User Stories, Regras de Negócio, Histórico | Estender RF-21, nova US, RN-044..RN-046 |
| `/docs/02-ARCHITECTURE.md` | Sim | Modelagem de Dados, estrutura | Colunas novas em `import_transactions`; `create_expense_with_installments` em services |
| `/docs/03-SPEC.md` + `specs/10` | Sim | Spec F07 (endpoints, service, frontend, testes) | Documentar classificação, ação e regras novas |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Visão geral | Registrar CR-049 |
| `/docs/05-DEPLOY-GUIDE.md` | Sim | Migrations | Migration 010 |
| `/docs/F07-v2-roadmap-importacao.md` | Sim | E-A, rastreabilidade | Marcar E-A como implementada (CR-049) |
| `CLAUDE.md` | Sim | Change Requests | Adicionar CR-049, mover CR-044 para o INDEX |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição da Mudança |
|------|---------|----------------------|
| Modificar | `backend/app/models.py` | `ImportTransaction`: `parcela_atual`, `parcela_total`, `expense_id_criado` |
| Criar | `backend/alembic/versions/010_add_import_installments.py` | Migration das três colunas |
| Modificar | `backend/app/services.py` | **Novo** `create_expense_with_installments()` (extraído do router de expenses) |
| Modificar | `backend/app/routers/expenses.py` | Passa a usar o service extraído (sem mudança de comportamento) |
| Modificar | `backend/app/import_service.py` | `parcelamento` em `CLASSIFICACOES_VALIDAS`; validação dos campos de parcela em `validate_ai_result` |
| Modificar | `backend/prompts/import_extraction_system.txt` | Regra de classificação `parcelamento` + precedência do `match_planejado` |
| Modificar | `backend/app/schemas.py` | Campos de parcela em `ImportTransactionResponse`/`ImportConfirmDecision`; ação nova; `planejados_criados` |
| Modificar | `backend/app/routers/imports.py` | Ação `criar_planejado_parcelado` no confirm |
| Modificar | `backend/tests/test_imports.py` | Testes da classificação, validação e confirm |
| Modificar | `backend/tests/test_services.py` | Testes do service extraído |
| Modificar | `frontend/src/types.ts` | Campos de parcela, ação nova, contador novo |
| Modificar | `frontend/src/utils/importReview.ts` | Grupo, decisão inicial, validação e payload da ação nova |
| Modificar | `frontend/src/utils/importReview.test.ts` | Testes dos helpers |
| Modificar | `frontend/src/components/imports/ImportReview.tsx` | Grupo "Compras parceladas", campos `x/y`, prévia do que será criado |
| Modificar | `frontend/src/components/imports/ImportResult.tsx` | Contador de planejados criados |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| Alterar | `import_transactions`: + `parcela_atual` INT NULL, `parcela_total` INT NULL, `expense_id_criado` VARCHAR(36) NULL | Sim (010) |

**Migration (resumo):**
```sql
ALTER TABLE import_transactions ADD COLUMN parcela_atual INTEGER NULL;
ALTER TABLE import_transactions ADD COLUMN parcela_total INTEGER NULL;
ALTER TABLE import_transactions ADD COLUMN expense_id_criado VARCHAR(36) NULL;
```
> Via `op.batch_alter_table()` — SQLite não suporta `ALTER` com FK (Troubleshooting do CLAUDE.md).

### 6.3 Contratos da API

**`POST /api/imports/{batch_id}/confirm`** — decisão nova:
```json
{ "id": "...", "acao": "criar_planejado_parcelado",
  "descricao": "Netshoes", "valor": 149.90, "data": "2026-07-15",
  "categoria": "Compras", "subcategoria": "Roupas",
  "parcela_atual": 3, "parcela_total": 10 }
```

- `parcela_total` obrigatório e > 1; `parcela_atual` obrigatório, entre 1 e `parcela_total` → senão 422
- Cria `parcela_total - parcela_atual + 1` despesas: a atual com status **Pago**, as seguintes **Pendente**
- `mes_referencia` = mês da `data` (consistente com RN-039); `vencimento` = `data` + N meses via `add_months`
- Parcela já existente no mês-alvo é pulada (RN-046) e não conta no resultado
- Auditoria: `expense_id_criado` recebe o id da parcela atual; `status` da transação → `confirmada`

**Resposta:** `{ "gastos_diarios_criados": N, "planejados_criados": N, "planejados_atualizados": N, "descartadas": N }`

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | Modelo + migration 010 (3 colunas) | — | `alembic upgrade head` e `downgrade 009` funcionam |
| CR-T-02 | Extrair `create_expense_with_installments()` para services e ligar o router de expenses | — | Testes existentes de expenses/parcelas verdes (sem mudança de comportamento) |
| CR-T-03 | `parcelamento` em `import_service` + prompt | CR-T-01 | `validate_ai_result` sanitiza campos de parcela; unit tests verdes |
| CR-T-04 | Schemas + ação `criar_planejado_parcelado` no confirm | CR-T-02, CR-T-03 | Endpoint cria a série e devolve os contadores |
| CR-T-05 | Testes backend (validação, confirm, dedup de parcela, 422) | CR-T-04 | Suíte backend verde |
| CR-T-06 | Frontend: types + helpers `importReview` + testes | CR-T-04 | Vitest verde |
| CR-T-07 | Frontend: grupo e edição na tela de revisão + resultado | CR-T-06 | Fluxo navegável, tsc e lint limpos |
| CR-T-08 | Revisão de segurança (checklist OWASP) | CR-T-07 | Checklist registrado neste CR |
| CR-T-09 | Validação runtime (HTTP + Playwright) | CR-T-07 | Registro na seção 8.1 |
| CR-T-10 | Code review pré-merge (`/code-review`) | CR-T-09 | Findings corrigidos ou justificados |
| CR-T-11 | Atualizar documentação (PRD, Arquitetura, Spec, Plano, Deploy Guide, roadmap, CLAUDE.md) | CR-T-10 | Docs sincronizados |

---

## 8. Critérios de Aceite

- [ ] IA classificando `parcelamento` produz transação com `parcela_atual`/`parcela_total` no staging
- [ ] `validate_ai_result` rebaixa para `gasto_diario` quando os campos de parcela estão ausentes ou incoerentes (`total <= 1`, `atual > total`, não inteiros)
- [ ] Confirm com `criar_planejado_parcelado` cria `total - atual + 1` despesas: a atual **Paga**, as seguintes **Pendentes**, com `mes_referencia` e `vencimento` corretos mês a mês
- [ ] Parcela já existente no mês-alvo não é recriada (RN-046)
- [ ] Decisão com parcela inválida retorna 422 sem gravar nada
- [ ] `expense_id_criado` gravado para auditoria; contador `planejados_criados` correto na resposta
- [ ] `POST /api/expenses/{year}/{month}` mantém exatamente o comportamento atual após o refactor (regressão)
- [ ] Revisão exibe o grupo "Compras parceladas" com a prévia do que será criado e permite editar `x/y`, valor, data e categoria
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a mudança (backend + frontend)
- [ ] Fluxo afetado exercitado em runtime antes do merge (HTTP + Playwright) — ver seção 8.1
- [ ] Revisão de código pré-merge (`/code-review`) executada — complexidade Alta
- [ ] Revisão de segurança (checklist OWASP) executada — endpoint alterado
- [ ] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. Critério pendente de evento posterior (ex: CI verde após push) mantém o CR "Em Implementação" até o follow-up.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Refactor do router de expenses quebra a criação manual de parcelas | Média | Alto | Service extraído preserva a lógica linha a linha; testes de regressão antes de seguir (CR-T-02) |
| 2 | Importar a fatura do mês seguinte duplica parcelas | Média | Alto | RN-046 (`expense_installment_exists`) + prompt dá precedência ao `match_planejado` quando o planejado já existe |
| 3 | IA marca assinatura recorrente (sem numeração) como parcelamento | Média | Médio | Prompt exige numeração explícita `x/y`; revisão obrigatória com prévia do que será criado |
| 4 | `parcela_total` errado gera dezenas de despesas | Baixa | Alto | Campos editáveis na revisão + prévia textual ("cria 8 parcelas até 02/2027") antes de confirmar |
| 5 | Parcela atual nasce Paga mas a fatura ainda não foi paga | Média | Baixo | Decisão consciente (RN-044), consistente com a RN-040; status editável na Visão Mensal |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-049` → `git revert [hash(es)]` → merge em `master` → push
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** commits da branch `feat/CR-049-importacao-parcelamentos`

### 10.2 Rollback de Migration

- **Migration afetada:** `010_add_import_installments.py`
- **Comando de downgrade:** `alembic downgrade 009`
- **Downgrade testado?** [ ] Sim / [ ] Nao — a preencher em CR-T-01
- **Downgrade e destrutivo?** [x] Sim (colunas de parcela e auditoria removidas do staging) — não afeta `expenses` já criadas

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** [x] Sim — apenas os campos de parcela/auditoria no staging de importação; as despesas parceladas já criadas permanecem
- **Backup necessario antes do deploy?** [ ] Nao (colunas novas, nullable)

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma
- **Acao de rollback:** N/A

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] `alembic current` mostra `009`
- [ ] Importação de extrato/fatura continua funcionando nas três classificações originais
- [ ] Criação manual de despesa parcelada continua criando as parcelas futuras
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-16 | Claude | CR criado a partir do item E-A do roadmap F07 v2; decisões de RN-044 (parcela atual Paga), RN-045 (vencimento = data da compra + N) e escopo único tomadas pelo autor |
