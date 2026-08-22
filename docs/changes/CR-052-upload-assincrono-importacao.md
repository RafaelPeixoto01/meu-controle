# Change Request — CR-052: Upload Assíncrono da Importação de Extratos (F07)

**Versão:** 1.2
**Data:** 2026-08-22
**Status:** Concluído
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

`POST /api/imports` chama a API da IA **dentro do request**, mantendo a conexão HTTP presa por até `IMPORT_TIMEOUT_SECONDS` (180s). Este CR move a extração para `BackgroundTasks` do FastAPI: o upload valida o PDF, grava o lote em `processando` e responde **202** imediatamente; `GET /api/imports/{batch_id}` vira o canal de polling do frontend.

Implementa o item **E-B** do [roadmap de evolução da F07 (v2)](../F07-v2-roadmap-importacao.md), que ataca a lacuna **L3 — confiabilidade**.

---

## 2. Classificação

| Campo            | Valor                                    |
|------------------|------------------------------------------|
| Tipo             | Mudança de Arquitetura                   |
| Origem           | Evolução do produto (roadmap F07 v2, E-B) |
| Urgência         | Próxima sprint                           |
| Complexidade     | Média (backend + migration + polling no frontend) |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

O upload é síncrono de ponta a ponta:

```
POST /api/imports → valida PDF → chama a IA (até 180s) → grava staging → 201 com o lote pronto
```

A UI só pode pedir ao usuário que não feche a página (`ImportUpload.tsx`, bloco `isUploading`). Se a IA falha, **nenhum lote é persistido** — a resposta traz `status="erro"` e o trabalho se perde por completo.

### Problema ou Necessidade

- Um proxy que corte a conexão antes de 180s, uma aba fechada ou uma rede instável perdem o lote inteiro — inclusive os tokens já gastos com a API.
- O usuário fica preso na tela sem poder navegar pelo app durante o processamento.
- Não existe registro de que uma importação foi tentada e falhou.
- Bloqueia o item **B-2** do roadmap (múltiplos arquivos por lote): sem processamento assíncrono, três arquivos seriam três esperas de 3 minutos em série.

### Situação Desejada (TO-BE)

```
POST /api/imports → valida PDF → grava lote 'processando' → 202 (só metadados)
                                       │
                                       └─ BackgroundTasks: IA → transações → 'pendente_revisao' | 'erro'

GET /api/imports/{id}  ←  polling do frontend a cada 3s
```

O usuário pode sair da página; ao voltar, um lote ainda em extração ou já pronto para revisão reaparece no banner. Falhas passam a ficar **registradas** no lote (`status='erro'` + `erro_mensagem`) em vez de se perderem na resposta HTTP — auditáveis, ainda que fora do banner (ver §12, finding 3).

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|---------------|----------------|
| 1  | `POST /api/imports` | 201 com o lote completo após a IA responder | **202** imediato com o lote em `processando`, sem transações |
| 2  | Chamada à IA | Dentro do request | `BackgroundTasks` in-process (sem broker) |
| 3  | Status do lote | `pendente_revisao`, `confirmado`, `descartado` | mais `processando` e `erro` |
| 4  | Falha da IA | `200 status="erro"`, nenhum lote persistido | Lote persistido em `erro` com `erro_mensagem` |
| 5  | `GET /api/imports/pending` | Só `pendente_revisao` | `pendente_revisao` + `processando` |
| 6  | `GET /api/imports/{id}` | Leitura simples | Canal de polling; resolve lote órfão (RN-048) |
| 7  | Frontend | Estágios `upload → review → result` | `upload → processing → review → result` com polling |
| 8  | Cópia da UI | "não feche esta página" | "pode fechar esta página — o lote continua processando" |

### 4.2 O que NÃO muda

- **RN-038** (staging obrigatório), **RN-039** (mês da data da compra), **RN-040** (match marca Pago + valor real), **RN-041** (receitas → `ignorar`), **RN-042** (dedup por fingerprint), **RN-043** (PDF nunca persistido — os bytes viajam só na closure da task, em memória).
- **RN-044/045/046** (compras parceladas, CR-049) — o confirm não é tocado.
- Validações de upload: extensão `.pdf`, magic bytes `%PDF-`, teto de 10MB, e os status codes 422/413. Continuam **síncronas**, no request.
- Rate limit de **5/min** no POST.
- Padrão F06 de indisponibilidade: `IMPORT_ENABLED=false` ou `ANTHROPIC_API_KEY` ausente → 200 com `status="indisponivel"`, nunca 5xx.
- Contratos de `POST /{id}/confirm` e `DELETE /{id}` — nenhuma mudança de código (o confirm já exige `pendente_revisao`, retornando 409 para `processando`).
- Nenhuma variável de ambiente nova.

### 4.3 Decisões de desenho

| Decisão | Justificativa |
|---------|---------------|
| `BackgroundTasks` in-process, sem Celery/RQ + Redis | O Railway roda um serviço único e o volume é de uso pessoal (poucos uploads/mês). Um broker adicionaria infraestrutura, custo e um segundo processo para manter, sem ganho proporcional |
| Lote órfão resolvido **na leitura**, sem job de limpeza | Um restart do container deixa lotes presos em `processando`. Resolver lazily no `GET` grava o `erro` uma vez e mantém `/pending` consistente, sem processo agendado |
| Janela de **30 min** para o lote órfão | Precisa ficar **acima** do pior caso da extração, senão a leitura marcaria como `erro` uma task ainda viva e o `_claim_batch` descartaria a extração já paga. Pior caso: 3 tentativas do `call_import_api` × 3 do SDK Anthropic × 180s ≈ 27 min. A janela de 10 min do desenho inicial era menor que isso (achado da revisão de código) |
| Factory de sessão injetada via `Depends` | A sessão do request já foi fechada quando a task roda. Sendo um `Depends`, os testes a sobrescrevem com o mesmo mecanismo já usado para `get_db` |
| Guarda de status na task antes de gravar (`_claim_batch`) | Se o usuário descartar o lote durante o processamento, a task não pode ressuscitá-lo como `pendente_revisao` — nem sobrescrevê-lo com `erro` |
| Sessão aberta em dois trechos curtos, com a chamada à IA entre eles | Segurar uma conexão do pool em transação pelos minutos da extração esgotaria o pool e exporia a task ao `idle_in_transaction_session_timeout` do PostgreSQL |

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Sim | Regras de Negócio, RF-21, histórico | Adicionar RN-047 e RN-048 |
| `/docs/02-ARCHITECTURE.md` | Sim | Padrões / decisões | ADR sobre `BackgroundTasks` sem broker |
| `/docs/specs/10-importacao-extratos.md` | Sim | Endpoints, Arquitetura, Persistência, Regras, Frontend | Contrato 202, statuses novos, migration 011 |
| `/docs/03-SPEC.md` | Não | — | É índice; a spec detalhada é a 10 |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Visão geral / CRs | Referenciar CR-052 |
| `/docs/05-DEPLOY-GUIDE.md` | Sim | Checklist de migrations | Migration 011 na lista |
| `/docs/F07-v2-roadmap-importacao.md` | Sim | E-B, Rastreabilidade, Changelog | Marcar E-B como implementada |
| `CLAUDE.md` | Sim | Change Requests (5 recentes) | Adicionar CR-052 |
| `/docs/changes/INDEX.md` | Sim | Histórico | Descer o CR mais antigo dos 5 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição da Mudança |
|------|---------|----------------------|
| Criar | `backend/alembic/versions/011_add_import_async.py` | Coluna `erro_mensagem` em `import_batches` |
| Modificar | `backend/app/models.py` | `ImportBatch.erro_mensagem` + statuses novos no comentário |
| Modificar | `backend/app/database.py` | `get_session_factory()` para trabalho fora do request |
| Modificar | `backend/app/import_service.py` | `process_import_batch()` (task) + `resolve_stale_batch()` + `STALE_PROCESSING_MINUTES` |
| Modificar | `backend/app/routers/imports.py` | POST → 202 + `BackgroundTasks`; GETs resolvem lote órfão |
| Modificar | `backend/app/crud.py` | `get_pending_import_batches` inclui `processando` |
| Modificar | `backend/app/schemas.py` | `ImportBatchSummary.erro_mensagem` |
| Modificar | `backend/tests/test_imports.py` | Fixture com `get_session_factory`; helpers de upload; casos novos |
| Modificar | `frontend/src/types.ts` | `ImportBatchStatus` + `erro_mensagem` |
| Modificar | `frontend/src/hooks/useImports.ts` | `useImportBatch` com `refetchInterval` |
| Criar | `frontend/src/components/imports/ImportProcessing.tsx` | Tela do estágio `processing` |
| Modificar | `frontend/src/components/imports/ImportUpload.tsx` | Banner distingue `processando` |
| Modificar | `frontend/src/pages/ImportView.tsx` | Estágio `processing` + transição por polling |
| Modificar | `frontend/src/utils/importReview.ts` | `nextStageForBatch()` (decisão pura de transição) |
| Modificar | `frontend/src/utils/importReview.test.ts` | Testes de `nextStageForBatch` |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| Adicionar coluna | `import_batches.erro_mensagem` (String(255), nullable) | Sim — **011** |
| Novos valores de `status` | `processando`, `erro` | Não — coluna já é `String(20)` e sem constraint |

**Migration:**
```sql
ALTER TABLE import_batches ADD COLUMN erro_mensagem VARCHAR(255);
```
Via `op.batch_alter_table` (SQLite não suporta `ALTER` com FK — CLAUDE.md).

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | Migration 011 + `ImportBatch.erro_mensagem` | — | `upgrade head` e `downgrade -1` rodam em SQLite local |
| CR-T-02 | `get_session_factory()` em `database.py` | — | Task consegue abrir sessão própria; testes sobrescrevem via `dependency_overrides` |
| CR-T-03 | `process_import_batch()` + `resolve_stale_batch()` no `import_service` | CR-T-01, CR-T-02 | Extração roda fora do request; erro grava `erro_mensagem`; lote descartado não ressuscita |
| CR-T-04 | Router: POST → 202 + `BackgroundTasks`; GETs resolvem lote órfão | CR-T-03 | POST responde 202 com lote `processando` sem transações |
| CR-T-05 | `crud.get_pending_import_batches` inclui `processando`; `schemas` expõe `erro_mensagem` | CR-T-01 | `/pending` lista lotes em processamento |
| CR-T-06 | Testes backend (fixture, helpers, casos novos) | CR-T-04, CR-T-05 | `pytest tests/ -v` verde, incluindo regressão dos testes de confirm/parcelamento |
| CR-T-07 | Frontend: tipos, `useImportBatch`, `ImportProcessing`, estágio no `ImportView`, banner | CR-T-04 | Fluxo upload → processando → revisão funciona com polling |
| CR-T-08 | Testes frontend (`nextStageForBatch`) | CR-T-07 | `npm test` verde |
| CR-T-09 | Revisão de segurança (OWASP) | CR-T-07 | Checklist do CLAUDE.md registrado neste CR |
| CR-T-10 | Validação runtime (Playwright) | CR-T-08 | Fluxo exercitado e registrado neste CR |
| CR-T-11 | `/code-review` no diff da branch | CR-T-10 | Findings corrigidos ou justificados neste CR |
| CR-T-12 | Atualizar documentação | CR-T-11 | PRD, Architecture, spec 10, roadmap, plano, deploy guide, CLAUDE.md, INDEX |

---

## 8. Critérios de Aceite

- [x] `POST /api/imports` responde **202** com o lote em `processando` e `transacoes: []`
- [x] A extração roda em background e o lote chega a `pendente_revisao` com as transações
- [x] Falha da IA grava o lote em `erro` com `erro_mensagem` legível (sem conteúdo do documento)
- [x] Documento sem transações identificáveis grava o lote em `erro`
- [x] `GET /api/imports/pending` lista `pendente_revisao` **e** `processando`
- [x] Lote em `processando` há mais de **30 min** é resolvido como `erro` na leitura (RN-048) — janela corrigida de 10 para 30 min na revisão de código
- [x] Descartar um lote durante o processamento não o ressuscita quando a task termina — vale no caminho de sucesso **e** no de erro
- [x] `POST /{id}/confirm` em lote `processando` retorna 409
- [x] Frontend faz polling a cada ~3s e transiciona para a revisão sozinho
- [x] Sair da página durante o processamento e voltar mostra o lote no banner de pendentes
- [x] Migration 011 aplica e reverte sem perda de dados existentes
- [x] Testes existentes continuam passando (regressão) — 202 backend, 70 Vitest
- [x] Novos testes cobrem a mudança — 9 backend + 6 Vitest
- [x] Fluxo afetado exercitado em runtime antes do merge (CR-037) — ver §11
- [x] Revisão de código pré-merge (`/code-review` no diff da branch) executada (CR-040) — ver §12
- [x] Revisão de segurança (checklist OWASP do CLAUDE.md) executada — ver §13
- [x] Documentos afetados foram atualizados — PRD v3.3, ARCHITECTURE v3.3 (ADR-021), spec 10, roadmap F07, Implementation Plan, Deploy Guide, CLAUDE.md, INDEX
- [x] CI verde após o push (`gh run watch`) — run 32598234651

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Restart do container deixa lotes órfãos em `processando` | Média | Baixo | RN-048: resolvido como `erro` na leitura após 30 min; usuário reenvia |
| 2 | Task in-process concorre com o request loop | Baixa | Baixo | FastAPI roda função síncrona em threadpool; volume pessoal + rate limit 5/min |
| 3 | Lote descartado durante o processamento ressuscita | Média | Médio | Task re-lê o status antes de gravar e aborta se não for mais `processando` |
| 4 | Polling do frontend não para e gera requests infinitos | Média | Médio | `refetchInterval` só continua enquanto `status === "processando"`; RN-048 garante estado terminal |
| 5 | Bytes do PDF vazam para log ao serem tratados na task | Baixa | Alto | `erro_mensagem` grava só `type(e).__name__`; nenhum log recebe `pdf_bytes` (RN-043) |
| 6 | Testes de confirm/parcelamento quebram com a mudança de contrato | Alta | Baixo | Helpers de teste passam a buscar o lote via `GET` após o POST; suíte inteira roda na verificação |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código

- **Método:** `git checkout -b hotfix/revert-CR-052` → `git revert [hash do merge]` → merge em `master` → push
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** commit de merge da branch `feat/CR-052-upload-assincrono-importacao`

### 10.2 Rollback de Migration

- **Migration afetada:** `011_add_import_async.py`
- **Comando de downgrade:** `alembic downgrade 010`
- **Downgrade testado?** [x] Sim — `upgrade head` → `downgrade -1` → `upgrade head` em SQLite local
- **Downgrade é destrutivo?** [x] Sim (parcialmente) — a coluna `erro_mensagem` é removida; são mensagens de diagnóstico de lotes que falharam, sem valor financeiro

### 10.3 Impacto em Dados

- **Dados serão perdidos no rollback?** [x] Sim (apenas `erro_mensagem`)
- **Detalhamento:** lotes que ficaram em `status='processando'` ou `'erro'` continuam na tabela com esses valores após o downgrade do código. O código anterior não os reconhece, mas também não quebra: `/pending` filtra por `pendente_revisao` e eles simplesmente não aparecem. Nenhum gasto ou despesa é afetado — lotes em staging nunca geraram lançamentos.
- **Backup necessário antes do deploy?** [ ] Não — a migration só adiciona coluna nullable
- **Procedimento de backup:** Deploy Guide seção 5 (`railway run pg_dump -Fc > backup.dump`)

### 10.4 Rollback de Variáveis de Ambiente

- **Variáveis novas/alteradas:** Nenhuma
- **Ação de rollback:** N/A

### 10.5 Verificação Pós-Rollback

- [ ] Aplicação acessível e funcional
- [ ] `alembic current` mostra `010`
- [ ] `POST /api/imports` volta a responder 201 com o lote completo
- [ ] Usuários existentes conseguem fazer login

---

## 11. Validação Runtime (CR-037)

Backend local em **SQLite** (`DATABASE_URL="sqlite:///./local.db"` — o `.env` aponta para produção) + `npm run dev`, com `call_import_api` substituído por um stub com **atraso de 8s**. A chamada à API Anthropic é a única parte do fluxo que este CR **não** altera, e não há `ANTHROPIC_API_KEY` no ambiente local; o atraso torna o estágio assíncrono observável, o que a API real (ou um mock instantâneo) não permitiria.

**Playwright — fluxo completo em `/import`:**

| # | Exercitado | Resultado |
|---|-----------|-----------|
| 1 | Upload de PDF | `POST /api/imports` → **202 Accepted** imediato; tela entra em "Interpretando o documento..." |
| 2 | Sair da página durante a extração (aba Dashboard) e voltar | Lote reaparece no banner como **"Acompanhar"** com spinner |
| 3 | Acompanhar até o fim | Transição automática para a revisão, sem interação |
| 4 | Confirmar o lote | "2 gastos diários criados · 8 parcelas criadas · 1 transação descartada" |

**Log do backend** — o contrato novo e o fim do polling, verificados na sequência real de requests:

```
POST /api/imports                    202 Accepted
[stub] extracao simulada; dormindo 8s
GET  /api/imports/pending            200 OK      (banner durante a extração)
GET  /api/imports/{id}               200 OK  x5  (polling de 3s — para sozinho ao chegar em pendente_revisao)
POST /api/imports/{id}/confirm       200 OK
```

**HTTP direto — RN-048 (lote órfão):**

| Cenário | Resultado |
|---------|-----------|
| Lote `processando` há 31 min → `GET /api/imports/{id}` | `erro` + "O processamento foi interrompido. Envie o arquivo novamente."; **persistido** no banco |
| Lote `processando` há 29 min → `GET` | Continua `processando` |
| `/pending` com os dois | Só o recente aparece |

**Estado final no banco:** lote `confirmado`, metadata gravada pela task (`modelo`, `tokens_input/output`, `tempo_processamento_ms`), 2 `DailyExpense` e 8 `Expense` criados.

**Console do browser:** 0 erros no fluxo. 2 warnings de `recharts` (dimensão de container), pré-existentes e originados da visita ao Dashboard — sem relação com este CR.

> **Observação da massa de teste:** o stub usou a subcategoria inexistente "Aplicativo de Transporte", e o `validate_ai_result` corretamente limpou o par categoria/subcategoria, exigindo preenchimento na revisão. Comportamento esperado do CR-046, não defeito.

---

## 12. Revisão de Código Pré-Merge (CR-040)

`/code-review high` sobre `git diff master...HEAD`. **6 findings; 5 corrigidos, 1 justificado.**

| # | Finding | Tratamento |
|---|---------|-----------|
| 1 | Polling parava para sempre se a **primeira** leitura falhasse (`refetchInterval` devolvia `false` com `data` undefined, e o `retry` global é 1) — usuário preso no spinner, com "Cancelar" descartando um lote provavelmente íntegro | **Corrigido:** segue tentando enquanto não houver status conhecido; o erro da tentativa aparece na tela |
| 2 | `STALE_PROCESSING_MINUTES = 10` menor que o pior caso real da extração (~27 min) — a leitura marcaria como `erro` uma task viva e o `_claim_batch` descartaria a extração já paga | **Corrigido:** 30 min, com a derivação documentada na constante |
| 3 | Lotes em `erro` invisíveis em qualquer UI, contradizendo a cópia "o lote reaparece aqui" | **Justificado + cópia corrigida:** o escopo do banner (`pendente_revisao` + `processando`, sem `erro`) foi decisão explícita do autor — lote que falha sai do banner e o usuário reenvia. A cópia é que prometia demais e foi ajustada |
| 4 | `_finish_with_error` sem a guarda de status do caminho de sucesso: cancelar durante a extração e a IA falhar em seguida sobrescrevia `descartado` com `erro` | **Corrigido:** guarda extraída para `_claim_batch` e aplicada aos dois caminhos + teste novo |
| 5 | `extraindo` invertido em `ImportProcessing`: `batch === undefined` contava como "extraindo", anunciando "Interpretando o documento" e um "Cancelar" destrutivo para lote que só ia abrir | **Corrigido:** `batch?.status === "processando"`; título neutro enquanto o status não chegou |
| 6 | Sessão aberta antes de `call_import_api` mantinha conexão do pool *idle in transaction* por minutos (risco de esgotar o pool e de `idle_in_transaction_session_timeout`) | **Corrigido:** sessão em dois trechos curtos, com a chamada à IA entre eles |

Após as correções: `pytest tests/` **202 passed**, `vitest` **70 passed**, `tsc --noEmit` limpo, `eslint` **0 erros**.

> **Follow-up registrado, fora do escopo deste CR:** o retry do `call_import_api` (3 tentativas) multiplica o `max_retries=2` **default do SDK Anthropic**, permitindo até 9 chamadas à API por importação. Reduzir a duplicação de camadas encurtaria o pior caso e o gasto, mas altera comportamento de chamada de IA definido nos CR-046/048 — candidato a CR próprio.

---

## 13. Revisão de Segurança (OWASP)

Obrigatória: o CR altera contrato de endpoint.

| Item | Resultado |
|------|-----------|
| Segredos hardcoded | OK — nada novo; `modelo` vem de `os.getenv("CLAUDE_MODEL", DEFAULT_MODEL)` |
| Inputs validados via Pydantic | OK — nenhum input novo; as validações de upload (extensão, magic bytes, 10MB) seguem **síncronas**, antes de qualquer trabalho |
| Tokens sensíveis fora do `localStorage` | Inalterado (refresh via cookie HttpOnly) |
| **Ownership** | OK — `crud.get_import_batch_by_id(db, batch_id, user_id)` filtra por `user_id` no polling **e** dentro da task (`_claim_batch`); lote de outro usuário → 404 (teste `test_lote_de_outro_usuario_retorna_404`) |
| Queries ORM parametrizadas | OK — `status.in_([...])`, sem SQL cru |
| CORS / headers de segurança | Inalterados |
| Novas dependências | **Nenhuma** — `BackgroundTasks` é do FastAPI/Starlette já instalado; sem broker, sem Redis |
| **RN-043 (PDF nunca persistido)** | OK — `pdf_bytes` só na closure da task; `erro_mensagem` grava apenas `type(e).__name__`, verificado por teste (`assert "boom" not in erro_mensagem`) |
| Rate limit | OK — `@limiter.limit("5/minute")` preservado no POST |

**Superfície nova considerada:** como o POST agora retorna rápido, um cliente poderia enfileirar trabalho de background mais depressa que antes, e o lote passa a ser gravado **antes** da extração (linhas em `import_batches` mesmo quando a IA falha). Ambos ficam limitados pelo mesmo rate limit de 5/min por usuário autenticado, e as linhas são metadados de staging que nunca viram lançamento.

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-22 | Claude | CR criado a partir do item E-B do roadmap F07 v2 |
| 2026-08-22 | Claude | Implementação backend: migration 011, `process_import_batch`, `resolve_stale_batch`, POST → 202, `/pending` com `processando` |
| 2026-08-22 | Claude | Implementação frontend: `useImportBatch` (polling), `ImportProcessing`, estágio novo na `ImportView`, banner |
| 2026-08-22 | Claude | Validação runtime via Playwright + HTTP — status: ✅ (§11) |
| 2026-08-22 | Claude | Revisão de código `/code-review high`: 6 findings, 5 corrigidos e 1 justificado (§12); revisão de segurança OWASP (§13) |
| 2026-08-22 | Claude | Documentos sincronizados: PRD v3.3 (RN-047/048), ARCHITECTURE v3.3 (ADR-021), spec 10, roadmap F07 (E-B ✅), Implementation Plan, Deploy Guide, CLAUDE.md, INDEX |
| 2026-08-22 | Claude | Merge em `master` e CI verde (run 32598234651) — CR concluído |
