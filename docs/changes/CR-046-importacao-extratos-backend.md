# Change Request — CR-046: Importação de Extratos e Faturas em PDF via IA (Backend — F07)

**Versão:** 1.0
**Data:** 2026-08-12
**Status:** Em Implementação
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Criar o backend da feature **F07 — Importação de Extratos e Faturas (PDF)**: o usuário faz upload do PDF de um extrato de conta ou fatura de cartão (Nubank, Itaú, Mercado Pago), o sistema interpreta as transações via IA (Claude, leitura nativa de PDF), armazena o resultado em staging para revisão e, após confirmação do usuário, cria **gastos diários** e/ou **atualiza gastos planejados** (status → Pago + valor real).

Este CR cobre **somente o backend** (API testável via HTTP). A UI será entregue no CR-047 (frontend).

> Design detalhado decidido em brainstorming registrado no plano aprovado (2026-08-12); espelhado na spec `docs/specs/10-importacao-extratos.md`.

---

## 2. Classificação

| Campo            | Valor                          |
|------------------|--------------------------------|
| Tipo             | Nova Feature                   |
| Origem           | Evolução do produto            |
| Urgência         | Próxima sprint                 |
| Complexidade     | Alta                           |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
Todo lançamento é manual: gastos diários são digitados um a um na view de Gastos Diários, e gastos planejados têm status/valor atualizados à mão na Visão Mensal. Não existe nenhum mecanismo de upload de arquivo no sistema.

### Problema ou Necessidade
Digitar dezenas de transações por mês é trabalhoso e propenso a esquecimento. Os bancos já fornecem PDFs de extrato/fatura com todas as transações.

### Situação Desejada (TO-BE)
Upload do PDF → IA extrai e classifica as transações (novo gasto diário / match com gasto planejado pendente / ignorar) → staging persistido e retomável → usuário revisa e confirma via API → sistema grava os lançamentos com deduplicação e trilha de auditoria.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)        | Depois (TO-BE)       |
|----|-------------------------|----------------------|----------------------|
| 1  | Entrada de dados        | Somente digitação manual | Upload de PDF (extrato/fatura) interpretado por IA |
| 2  | Modelo de dados         | Sem tabelas de importação | Novas tabelas `import_batches` e `import_transactions` (migration 009) |
| 3  | API                     | Sem endpoints de importação | Router `/api/imports` (upload, pending, get, confirm, delete) |
| 4  | Gasto planejado pago    | Status/valor atualizados manualmente | Confirmação da importação marca Pago + atualiza valor real |
| 5  | Deduplicação            | Inexistente | Fingerprint por transação (sha256 de user+data+valor+descrição normalizada) |

### 4.2 O que NÃO muda

- Tabelas existentes (`expenses`, `daily_expenses`, etc.) — **nenhuma coluna nova**; auditoria fica nas tabelas de import
- CRUD manual de gastos diários e planejados (continua funcionando igual)
- Análise financeira IA (CR-032) — serviço separado, apenas padrões reutilizados
- Frontend — intocado neste CR (entra no CR-047)

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária |
|-----------------------------------|------------|-----------------|-----------------|
| `/docs/01-PRD.md`                 | Sim | RFs, User Stories, Regras de Negócio, Glossário, Roadmap (Fase 7), histórico | Novo módulo F07 (RF-32..), US e RNs de importação |
| `/docs/02-ARCHITECTURE.md`        | Sim | Estrutura de pastas, Modelagem de Dados, ADRs | Tabelas novas + ADR-018 (parsing por IA, sem parser por banco) |
| `/docs/03-SPEC.md`                | Sim | Índice de specs | Nova linha para `specs/10-importacao-extratos.md` (F07) |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Visão geral / grupos | Registrar CR-046 e tarefas |
| `/docs/05-DEPLOY-GUIDE.md`        | Sim | Variáveis de ambiente / migrations | `IMPORT_ENABLED`, `IMPORT_TIMEOUT_SECONDS`; migration 009 |
| `CLAUDE.md`                       | Sim | Change Requests, estrutura, env vars | Adicionar CR-046 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                | Descrição da Mudança |
|-----------|---------------------------------------------------|----------------------|
| Modificar | `backend/app/models.py`                           | Modelos `ImportBatch` e `ImportTransaction` + relationships em `User` |
| Criar     | `backend/alembic/versions/009_add_import_tables.py` | Migration das duas tabelas |
| Modificar | `backend/app/schemas.py`                          | Schemas de request/response de importação |
| Criar     | `backend/app/import_service.py`                   | Fingerprint/normalização, montagem de prompt, chamada Anthropic com PDF (document block), validação do JSON retornado, dedup |
| Criar     | `backend/prompts/import_extraction_system.txt`    | System prompt da extração |
| Criar     | `backend/prompts/import_extraction_user.txt`      | User prompt (placeholders: categorias, planejados pendentes) |
| Criar     | `backend/app/routers/imports.py`                  | Endpoints upload/pending/get/confirm/delete |
| Modificar | `backend/app/main.py`                             | Registrar router |
| Modificar | `backend/app/crud.py`                             | Funções de acesso a batches/transactions |
| Criar     | `backend/tests/test_imports.py`                   | Testes (mock da API Anthropic) |

### 6.2 Banco de Dados

| Ação  | Descrição | Migration Necessária? |
|-------|-----------|-----------------------|
| Criar | Tabela `import_batches` (lote de importação: arquivo, banco/tipo detectado, status, metadados IA) | Sim (009) |
| Criar | Tabela `import_transactions` (transações extraídas: dados, sugestão da IA, fingerprint, status, FKs de auditoria) | Sim (009) |

**Migration (resumo):**
```sql
CREATE TABLE import_batches (
  id VARCHAR(36) PK, user_id VARCHAR(36) FK users ON DELETE CASCADE,
  filename VARCHAR(255), banco_detectado VARCHAR(50), tipo_documento VARCHAR(20),
  status VARCHAR(20) DEFAULT 'pendente_revisao',
  tokens_input INT NULL, tokens_output INT NULL, modelo VARCHAR(50),
  tempo_processamento_ms INT NULL, created_at, updated_at
);
CREATE TABLE import_transactions (
  id VARCHAR(36) PK, batch_id VARCHAR(36) FK import_batches ON DELETE CASCADE,
  user_id VARCHAR(36) FK users ON DELETE CASCADE,
  data DATE, descricao VARCHAR(255), valor NUMERIC(10,2),
  classificacao VARCHAR(20), motivo_ignorar VARCHAR(255) NULL,
  expense_id_sugerido VARCHAR(36) NULL,
  categoria VARCHAR(50) NULL, subcategoria VARCHAR(50) NULL, metodo_pagamento VARCHAR(30) NULL,
  fingerprint VARCHAR(64), status VARCHAR(20) DEFAULT 'pendente',
  daily_expense_id_criado VARCHAR(36) NULL, expense_id_atualizado VARCHAR(36) NULL,
  created_at, updated_at
);
CREATE INDEX ix_import_tx_user_fingerprint ON import_transactions (user_id, fingerprint);
CREATE INDEX ix_import_batches_user_status ON import_batches (user_id, status);
```

### 6.3 Contratos da API (resumo — detalhe na spec F07)

| Endpoint | Verbo | Descrição |
|----------|-------|-----------|
| `/api/imports` | POST (multipart) | Upload do PDF → parse IA → lote `pendente_revisao` (201). Rate limit 5/min. |
| `/api/imports/pending` | GET | Lotes pendentes de revisão (retomada) |
| `/api/imports/{batch_id}` | GET | Lote + transações |
| `/api/imports/{batch_id}/confirm` | POST | Aplica decisões revisadas (cria DailyExpense / atualiza Expense / descarta) |
| `/api/imports/{batch_id}` | DELETE | Descarta lote pendente (204) |

**Regras principais:**
- Upload: somente PDF (extensão + magic bytes `%PDF-`), máx. 10MB; PDF processado em memória e **nunca persistido**
- Feature flag `IMPORT_ENABLED` (default true) + exige `ANTHROPIC_API_KEY`; timeout `IMPORT_TIMEOUT_SECONDS` (default 90s); modelo `CLAUDE_MODEL`
- IA recebe: PDF (document block) + categorias/subcategorias/métodos válidos + gastos planejados Pendente/Atrasado do usuário
- Dedup: fingerprint `sha256(user_id|data|valor|descricao_normalizada)`; se já **confirmado** em lote anterior → transação nasce `duplicada`
- Confirm: `criar_gasto_diario` (mes_referencia = mês da **data da compra**; valida par categoria/subcategoria e método), `atualizar_planejado` (ownership; status→Pago, valor→real), `descartar`
- Erros da IA seguem padrão CR-032: nunca 5xx; resposta com `status="erro"` e reason

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When |
|---------|-------------------------------------|------------|-----------|
| CR-T-01 | Atualizar PRD + criar spec F07 (`docs/specs/10-importacao-extratos.md`) + índice 03-SPEC | — | Docs criados/atualizados seguindo templates |
| CR-T-02 | Modelos `ImportBatch`/`ImportTransaction` + migration 009 | CR-T-01 | `alembic upgrade head` e `downgrade -1` funcionam |
| CR-T-03 | `import_service.py` + prompts (extração IA, fingerprint, dedup, validação) | CR-T-02 | Unit tests do serviço passam (API mockada) |
| CR-T-04 | Router `/api/imports` + schemas + registro no main | CR-T-03 | Endpoints respondem com status codes corretos |
| CR-T-05 | Testes pytest (upload, dedup, confirm, ownership, flag desligada) | CR-T-04 | Suíte completa verde |
| CR-T-06 | Revisão de segurança (checklist OWASP) | CR-T-05 | Checklist registrado neste CR |
| CR-T-07 | Validação runtime via HTTP com PDF real | CR-T-05 | Registro do resultado neste CR |
| CR-T-08 | Code review pré-merge (`/code-review`) | CR-T-07 | Findings corrigidos/justificados |
| CR-T-09 | Atualizar documentação (Arquitetura, Plano, Deploy Guide, CLAUDE.md) | CR-T-08 | Docs sincronizados |

---

## 8. Critérios de Aceite

- [ ] Upload de PDF válido retorna 201 com lote `pendente_revisao` e transações classificadas (gasto_diario / match_planejado / ignorar)
- [ ] Upload de arquivo não-PDF ou >10MB retorna 422/413 sem chamar a IA
- [ ] Re-upload com transações já confirmadas marca-as como `duplicada`
- [ ] Confirm cria `DailyExpense` no mês da data da compra e atualiza `Expense` (status Pago + valor real), gravando FKs de auditoria
- [ ] Confirm/get/delete verificam ownership (404 para lote de outro usuário)
- [ ] `IMPORT_ENABLED=false` ou `ANTHROPIC_API_KEY` ausente → resposta de indisponibilidade sem 5xx
- [ ] PDF não é persistido em disco nem no banco
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a mudança
- [ ] Fluxo afetado exercitado em runtime antes do merge — descrever O QUE foi validado e o resultado (chamada HTTP aos endpoints)
- [ ] Revisão de código pré-merge (`/code-review` no diff da branch) executada — registrar findings corrigidos/justificados
- [ ] Revisão de segurança (checklist OWASP do CLAUDE.md) executada
- [ ] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. Critério pendente de evento posterior (ex: CI verde após push) mantém o CR "Em Implementação" até o follow-up.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|----|--------------------------|---------------|---------|-----------|
| 1  | IA extrai transações erradas (valor/data/classificação) | Média | Médio | Tela de revisão obrigatória (CR-047); staging nunca grava direto nas tabelas finais |
| 2  | Fatura grande estoura `max_tokens` da resposta | Média | Médio | `max_tokens` alto (8192) + reparo de JSON truncado (padrão CR-032) + limite de 10MB por arquivo; documentar limitação |
| 3  | Custo de API por upload | Baixa | Baixo | Rate limit 5/min; uso pessoal (poucos uploads/mês) |
| 4  | Subcategorias duplicadas entre categorias geram categoria errada | Média | Baixo | Prompt exige par categoria+subcategoria; backend valida o par (não deriva só da subcategoria) |
| 5  | Dados sensíveis do PDF | Baixa | Alto | PDF processado em memória e descartado; só transações extraídas persistem; nada de PDF em log |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-046` → `git revert [hash(es)]` → merge em `master` → push
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** commits da branch `feat/CR-046-importacao-extratos-backend`

### 10.2 Rollback de Migration

- **Migration afetada:** `009_add_import_tables.py`
- **Comando de downgrade:** `alembic downgrade 008`
- **Downgrade testado?** [ ] Sim / [ ] Nao
- **Downgrade e destrutivo?** [x] Sim (tabelas de import e seu histórico são removidas) — não afeta `expenses`/`daily_expenses`

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** [x] Sim — apenas staging/auditoria de importações; lançamentos já confirmados permanecem
- **Backup necessario antes do deploy?** [ ] Nao (tabelas novas, sem alteração nas existentes)

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** `IMPORT_ENABLED` (opcional, default true), `IMPORT_TIMEOUT_SECONDS` (opcional, default 90)
- **Acao de rollback:** remover as variáveis do Railway (ou setar `IMPORT_ENABLED=false` para desativar a feature sem rollback de código)

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] `alembic current` mostra `008`
- [ ] CRUD de gastos diários e planejados funcionando
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data       | Autor  | Descrição |
|------------|--------|-----------|
| 2026-08-12 | Claude | CR criado (design aprovado em brainstorming; entrega em 2 CRs: 046 backend, 047 frontend) |
