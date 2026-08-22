# Change Request — CR-052: Upload Assíncrono da Importação de Extratos (F07)

**Versão:** 1.0
**Data:** 2026-08-22
**Status:** Em Implementação
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

O usuário pode sair da página; ao voltar, o lote reaparece no banner de pendentes com o estado atual. Falhas ficam registradas no lote (`status='erro'` + `erro_mensagem`) em vez de sumirem.

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
| Janela de 10 min para o lote órfão | Folga confortável sobre `IMPORT_TIMEOUT_SECONDS` (180s) somado aos 2 retries do `call_import_api` |
| Factory de sessão injetada via `Depends` | A sessão do request já foi fechada quando a task roda. Sendo um `Depends`, os testes a sobrescrevem com o mesmo mecanismo já usado para `get_db` |
| Guarda de status na task antes de gravar | Se o usuário descartar o lote durante o processamento, a task não pode ressuscitá-lo como `pendente_revisao` |

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

- [ ] `POST /api/imports` responde **202** com o lote em `processando` e `transacoes: []`
- [ ] A extração roda em background e o lote chega a `pendente_revisao` com as transações
- [ ] Falha da IA grava o lote em `erro` com `erro_mensagem` legível (sem conteúdo do documento)
- [ ] Documento sem transações identificáveis grava o lote em `erro`
- [ ] `GET /api/imports/pending` lista `pendente_revisao` **e** `processando`
- [ ] Lote em `processando` há mais de 10 min é resolvido como `erro` na leitura (RN-048)
- [ ] Descartar um lote durante o processamento não o ressuscita quando a task termina
- [ ] `POST /{id}/confirm` em lote `processando` retorna 409
- [ ] Frontend faz polling a cada ~3s e transiciona para a revisão sozinho
- [ ] Sair da página durante o processamento e voltar mostra o lote no banner de pendentes
- [ ] Migration 011 aplica e reverte sem perda de dados existentes
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a mudança
- [ ] Fluxo afetado exercitado em runtime antes do merge (CR-037)
- [ ] Revisão de código pré-merge (`/code-review` no diff da branch) executada (CR-040)
- [ ] Revisão de segurança (checklist OWASP do CLAUDE.md) executada
- [ ] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Restart do container deixa lotes órfãos em `processando` | Média | Baixo | RN-048: resolvido como `erro` na leitura após 10 min; usuário reenvia |
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
- **Downgrade testado?** [ ] Sim / [ ] Não
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

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-22 | Claude | CR criado a partir do item E-B do roadmap F07 v2 |
