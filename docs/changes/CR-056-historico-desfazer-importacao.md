# Change Request — CR-056: Histórico e Desfazer da Importação

**Versão:** 1.0
**Data:** 2026-09-25
**Status:** Concluído
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Primeira metade do **E-D** do [roadmap F07 v2](../F07-v2-roadmap-importacao.md) — a rede de segurança da importação:

- **Histórico:** `GET /api/imports` paginado, com o resumo de cada lote. Hoje só existe `/pending`, então tudo o que já foi importado some da interface.
- **Desfazer:** `POST /api/imports/{id}/undo` para lote `confirmado`, com prévia (`GET /api/imports/{id}/undo-preview`). Remove o que o lote criou e **restaura** o estado anterior dos planejados que ele conciliou. Lançamentos alterados ou apagados depois da importação são preservados e reportados, em vez de bloquear o undo inteiro.

A outra metade do E-D — a **reconciliação de total do documento** — vai no CR-057, porque mexe no prompt da IA e tem risco independente (decisão do autor, 2026-09-25).

---

## 2. Classificação

| Campo        | Valor                                                |
|--------------|------------------------------------------------------|
| Tipo         | Nova Feature                                         |
| Origem       | Evolução do produto (roadmap F07 v2, item E-D)       |
| Urgência     | Próxima sprint                                       |
| Complexidade | Alta (migration + 3 endpoints + tela nova + mudança no confirm) |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

- Depois do confirm, o lote sai do `/pending` e **não aparece em lugar nenhum**. Não há como ver o que foi importado, de qual arquivo, nem quando.
- Um confirm errado — o arquivo do mês errado, a mesma fatura confirmada por dois caminhos, 60 lançamentos com a categoria errada — só se resolve apagando à mão, um por um, em duas telas (Gastos Diários e Planejados), e **sem como restaurar** o status e o valor dos planejados que a conciliação marcou como Pago.
- Os campos de auditoria (`daily_expense_id_criado`, `expense_id_atualizado`, `expense_id_criado`) são gravados desde o CR-046/049, mas nunca lidos.

### Problema ou Necessidade

Os campos de auditoria **não bastam** para um undo correto — foi o que a exploração deste CR mostrou, e é o motivo da ADR-022:

1. **Só a parcela âncora é registrada.** `criar_planejado_parcelado` grava em `expense_id_criado` apenas a parcela informada; as N parcelas futuras que `services.create_expense_with_installments` cria não deixam rastro no lote.
2. **`expense_id_criado` pode apontar para algo que o lote NÃO criou.** Pela RN-046, se a parcela já existia, ela é **conciliada** (status e valor sobrescritos) e o id dela vai para `expense_id_criado` do mesmo jeito. Um undo guiado por esse campo **apagaria um lançamento pré-existente do usuário**.
3. **Não há estado anterior.** A conciliação (`atualizar_planejado` e a da RN-046) sobrescreve status e valor sem guardar o que havia antes.
4. **Não há como saber se o usuário mexeu depois.** `updated_at` não serve de sinal: a auto-detecção de status (RF-05) persiste `Pendente → Atrasado` sozinha a cada leitura do mês, então toda parcela futura vencida pareceria "editada".

### Situação Desejada (TO-BE)

- A tela de importação ganha a seção **"Importações anteriores"**, com cada lote, seu status e seus contadores.
- Um lote confirmado pode ser **desfeito**. Antes, uma prévia lista exatamente o que será removido, o que será restaurado e o que será mantido (e por quê). Depois, o lote fica `revertido` e o mesmo documento pode ser importado de novo.
- O confirm passa a registrar cada efeito num **diário** (`import_effects`), com o estado anterior e uma assinatura do que foi gravado — a fonte da verdade do undo.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|---------------|----------------|
| 1  | Lotes já processados | Invisíveis (só `/pending`) | `GET /api/imports?page=&page_size=` com todos os lotes do usuário, mais recentes primeiro |
| 2  | Registro do confirm | IDs de auditoria na transação (só a âncora da série) | + uma linha em `import_effects` por efeito: gasto criado, planejado criado (cada parcela), planejado conciliado (com status/valor anteriores) |
| 3  | Desfazer | Inexistente | Prévia + `POST /api/imports/{id}/undo`; lote → `revertido` |
| 4  | Status do lote | … `confirmado`, `descartado`, `erro` | + `revertido` |
| 5  | Status da transação | `pendente`, `confirmada`, `descartada`, `duplicada` | + `revertida` (deixa de contar para a dedup — RN-052) |
| 6  | `import_batches` | — | + `confirmado_em`, `revertido_em` (nullable) |
| 7  | Tela de importação | Upload + banner de pendentes | + seção "Importações anteriores" e diálogo de desfazer |

### 4.2 Regras do desfazer (RN-051)

Para cada efeito registrado no diário do lote:

| Situação do lançamento hoje | Efeito "criado" | Efeito "conciliado" | Contador |
|-----------------------------|-----------------|---------------------|----------|
| Igual ao que o confirm gravou (assinatura bate) | **Removido** | **Restaurado** (status e valor anteriores) | removidos / restaurados |
| Alterado depois da importação (assinatura difere) | Mantido | Mantido | `preservados` |
| Não existe mais (usuário apagou) | Nada a fazer | Nada a fazer | `ja_removidos` |

- **Assinatura** = sha256 dos campos que o usuário pode alterar, no momento do confirm. Em `Expense`, o status entra **normalizado**: `Pendente` e `Atrasado` contam como o mesmo estado ("em aberto"), porque a RF-05 alterna entre eles sem ação do usuário. `Pago` é distinto — parcela futura paga à mão depois da importação é **preservada** (risco listado no roadmap).
- "Alterado depois" cobre também a alteração feita por **outro lote**: se o lote B concilia uma parcela que o lote A criou, desfazer A preserva essa parcela. Desfazer B antes a restaura, e desfazer A em seguida a remove.
- **Transação → `revertida`** somente se nenhum efeito dela foi preservado. Se algum lançamento dela foi mantido, a transação continua `confirmada`: é o que impede que reimportar o documento lance **de novo** o que ficou (RN-042).
- **Só lotes com diário.** Lotes confirmados antes deste CR não têm diário (`confirmado_em` nulo) e **não podem ser desfeitos** — o undo sem o diário cairia exatamente nos furos da seção 3. Eles aparecem no histórico, sem o botão.
- **Regras aprendidas (CR-054) não são revertidas** (decisão do autor, 2026-09-25). Uma regra errada aparece com o badge "aprendido" na próxima revisão e é corrigida no confirm seguinte (a última decisão vence).
- **Atômico:** o undo inteiro roda numa transação; qualquer erro não deixa o lote meio desfeito.
- **Ordem inversa entre lotes dependentes** (acrescentado na revisão de código, finding #1): se um lote confirmado **depois** tem efeito num lançamento que este criou ou conciliou, o undo deste → 409 "Desfaça antes a importação …". Na ordem inversa, o undo do mais recente devolve o lançamento exatamente ao estado que o mais antigo gravou, e o undo do mais antigo o remove.

### 4.3 Contratos

**`GET /api/imports?page=1&page_size=20`** → 200

```json
{
  "items": [
    {
      "id": "...", "filename": "fatura-jul.pdf", "banco_detectado": "Nubank",
      "tipo_documento": "fatura", "status": "confirmado", "erro_mensagem": null,
      "created_at": "...", "confirmado_em": "...", "revertido_em": null,
      "total_transacoes": 42, "confirmadas": 38, "descartadas": 3,
      "duplicadas": 1, "revertidas": 0,
      "pode_desfazer": true
    }
  ],
  "total": 7, "page": 1, "page_size": 20
}
```

- Todos os status, ordenados por `created_at` desc (desempate por `id`). `page >= 1`, `1 <= page_size <= 50` (senão 422).
- Contadores numa única query agregada para a página (sem N+1).
- Aplica a RN-048 aos lotes da página (lote órfão em `processando` aparece como `erro`, igual ao `/pending`).

**`GET /api/imports/{id}/undo-preview`** → 200 | 404 (outro usuário) | 409 (não é `confirmado`, ou lote sem diário)

```json
{
  "itens": [
    { "entidade": "gasto_diario", "efeito": "criado", "acao": "remover",
      "descricao": "Padaria Stella", "valor": 23.50, "data": "2026-07-28",
      "parcela_atual": null, "parcela_total": null, "status_anterior": null },
    { "entidade": "planejado", "efeito": "conciliado", "acao": "restaurar",
      "descricao": "Energia elétrica", "valor": 187.32, "data": "2026-07-15",
      "status_anterior": "Pendente", "valor_anterior": 200.00 },
    { "entidade": "planejado", "efeito": "criado", "acao": "preservar",
      "descricao": "Netshoes", "valor": 149.90, "data": "2026-09-15",
      "parcela_atual": 5, "parcela_total": 10 }
  ],
  "gastos_diarios_removidos": 1, "planejados_removidos": 0,
  "planejados_restaurados": 1, "preservados": 1, "ja_removidos": 0
}
```

- `acao ∈ {remover, restaurar, preservar, ja_removido}`. `data` é a data do gasto ou o vencimento do planejado. Para `ja_removido` os campos descritivos vêm da transação importada (o lançamento não existe mais).

**`POST /api/imports/{id}/undo`** → 200 | 404 | 409 — mesmos contadores da prévia, calculados de novo no momento da execução (a prévia é informativa; o que vale é o estado na hora do undo).

### 4.4 O que NÃO muda

- Regras de classificação, prompt da IA, memória de categorização (CR-054) e detecção de já pago (CR-055).
- Contrato do `POST /confirm` (request e response) e seus 409/422. Ele só passa a **também** gravar o diário e `confirmado_em` — e, desde a revisão de código, a arredondar `valor` a 2 casas antes de gravar (valor que arredonda para 0 → 422). Sem efeito para valores com até 2 casas, que é o que a UI envia.
- `DELETE /api/imports/{id}` (descartar) — continua recusando lote `confirmado` (409) e passa a recusar também `revertido`; desfazer é outra operação.
- `/pending` — continua listando só `processando` e `pendente_revisao`.
- Assinatura de `services.create_expense_with_installments` para o cadastro manual: o parâmetro novo (`efeitos`) é opcional e o retorno é o mesmo.
- Fingerprint (RN-042) e seu cálculo. Só o conjunto de status que conta como "já confirmado" continua `confirmada` — `revertida` fica fora por construção.

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Sim | Cabeçalho, RF-21, US, RN, Histórico | RF-21 detalhado com histórico/undo; US-30; RN-051 e RN-052; v3.6 |
| `/docs/02-ARCHITECTURE.md` | Sim | Modelagem (ImportBatch, ImportTransaction, **ImportEffect**), estrutura (`import_undo.py`), ADRs | ADR-022 (diário de efeitos) |
| `/docs/03-SPEC.md` | Sim | Índice da F07 | Referenciar CR-056 |
| `/docs/specs/10-importacao-extratos.md` | Sim | Endpoints, ciclo de vida, persistência, regras, testes, frontend | Seção "Histórico e desfazer" |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Header + tabela de visão geral | Linha CR-056 |
| `/docs/05-DEPLOY-GUIDE.md` | Sim | Migrations | Nota da migration 013 |
| `/docs/F07-v2-roadmap-importacao.md` | Sim | E-D, rastreabilidade | E-D parcial (histórico + undo), "Como ficou" |
| `CLAUDE.md` | Sim | Change Requests, estrutura (migrations 001..013, `import_undo`) | Adicionar CR-056, mover CR-051 para o INDEX |
| `docs/changes/INDEX.md` | Sim | Lista | Receber CR-051 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho | Descrição |
|------|---------|-----------|
| Criar | `backend/alembic/versions/013_add_import_effects.py` | Tabela `import_effects` + `confirmado_em`/`revertido_em` em `import_batches` |
| Modificar | `backend/app/models.py` | `ImportEffect`; colunas novas em `ImportBatch`; status `revertido`/`revertida` nos comentários |
| Criar | `backend/app/import_undo.py` | `entity_signature`, registro de efeitos, `plan_undo` (puro sobre o estado lido) e `apply_undo` |
| Modificar | `backend/app/services.py` | `SeriesEffects` + parâmetro opcional `efeitos` em `create_expense_with_installments` |
| Modificar | `backend/app/routers/imports.py` | Confirm grava o diário; `GET ""` (histórico), `GET /{id}/undo-preview`, `POST /{id}/undo` |
| Modificar | `backend/app/crud.py` | Histórico paginado + contadores agregados; `get_daily_expenses_by_ids`/`get_expenses_by_ids` (em fatias, filtrados por usuário); `get_import_batch_for_update`; `get_later_batch_touching` |
| Modificar | `backend/app/schemas.py` | `ImportHistoryItem`, `ImportHistoryPage`, `ImportUndoItem`, `ImportUndoPreview`, `ImportUndoResponse` |
| Criar | `backend/tests/test_import_history_undo.py` | Testes do histórico, do diário e do undo |
| Modificar | `frontend/src/types.ts` | Tipos novos + status `revertido`/`revertida` |
| Modificar | `frontend/src/services/api.ts` | `fetchImportHistory`, `fetchUndoPreview`, `undoImport` |
| Modificar | `frontend/src/hooks/useImports.ts` | `useImportHistory`, `useUndoPreview`, `useUndoImport`; invalidar histórico em upload/confirm/descarte |
| Criar | `frontend/src/components/imports/ImportHistory.tsx` | Lista paginada com status, contadores e ação "Desfazer" |
| Criar | `frontend/src/components/imports/ImportUndoDialog.tsx` | Prévia agrupada por ação + confirmação |
| Modificar | `frontend/src/pages/ImportView.tsx` | Renderiza o histórico no estágio de upload |
| Criar | `frontend/src/utils/importHistory.ts` (+ `.test.ts`) | Helpers puros: rótulos de status, resumo de contadores, agrupamento da prévia, texto do resultado |

### 6.2 Banco de Dados

| Ação | Descrição | Migration? |
|------|-----------|-----------|
| Criar tabela | `import_effects` | Sim (013) |
| Adicionar colunas | `import_batches.confirmado_em`, `import_batches.revertido_em` (DateTime, nullable) | Sim (013) |
| Novos valores de status | `revertido` (lote), `revertida` (transação) | Não — `String(20)` sem constraint |

```sql
CREATE TABLE import_effects (
  id              VARCHAR(36) PRIMARY KEY,
  batch_id        VARCHAR(36) NOT NULL REFERENCES import_batches(id) ON DELETE CASCADE,
  transaction_id  VARCHAR(36) NOT NULL REFERENCES import_transactions(id) ON DELETE CASCADE,
  user_id         VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tipo            VARCHAR(30) NOT NULL,  -- gasto_diario_criado | planejado_criado | planejado_conciliado
  entidade_id     VARCHAR(36) NOT NULL,  -- sem FK: o lançamento pode ser apagado pelo usuário
  assinatura      VARCHAR(64) NOT NULL,  -- sha256 do estado gravado pelo confirm
  status_anterior VARCHAR(20),           -- só em planejado_conciliado
  valor_anterior  NUMERIC(10,2),         -- só em planejado_conciliado
  created_at      DATETIME NOT NULL
);
CREATE INDEX ix_import_effects_batch ON import_effects (batch_id);
ALTER TABLE import_batches ADD COLUMN confirmado_em DATETIME;
ALTER TABLE import_batches ADD COLUMN revertido_em DATETIME;
```

`entidade_id` sem FK é deliberado: aponta para `daily_expenses` **ou** `expenses` conforme o `tipo`, e o usuário pode apagar o lançamento a qualquer momento — o diário precisa sobreviver a isso para o undo reportar `ja_removido`.

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | Migration 013 + `ImportEffect` + colunas no `ImportBatch` | — | `upgrade head` e `downgrade -1` rodam em SQLite local |
| CR-T-02 | `SeriesEffects` em `services.create_expense_with_installments` | — | Testes de `test_services` seguem verdes; efeitos da série distinguem criada × conciliada |
| CR-T-03 | `import_undo.py`: assinatura, registro, `plan_undo`, `apply_undo` | CR-T-01, 02 | Testes unitários da assinatura e do plano |
| CR-T-04 | Confirm grava o diário e `confirmado_em` | CR-T-03 | Um efeito por gasto, por parcela criada e por conciliação, com estado anterior |
| CR-T-05 | Endpoints: histórico, prévia, undo | CR-T-04 | Status codes e payloads da seção 4.3; ownership 404 |
| CR-T-06 | Testes backend do CR | CR-T-05 | Cenários da seção 8 cobertos |
| CR-T-07 | Frontend: tipos, api, hooks | CR-T-05 | `tsc` limpo |
| CR-T-08 | Frontend: `ImportHistory`, `ImportUndoDialog`, helpers + Vitest | CR-T-07 | Vitest verde, lint limpo |
| CR-T-09 | Validação runtime (HTTP + Playwright) | CR-T-08 | Registro na seção 11 |
| CR-T-10 | Revisão de código + segurança | CR-T-09 | Findings tratados na seção 12 |
| CR-T-11 | Documentação | CR-T-10 | Todos os documentos da seção 5 atualizados |

---

## 8. Critérios de Aceite

- [x] `GET /api/imports` lista todos os lotes do usuário, paginados, mais recentes primeiro, com contadores por status de transação e `pode_desfazer`
- [x] Lotes de outro usuário nunca aparecem no histórico; prévia/undo de lote alheio → 404
- [x] Confirm grava um efeito por gasto diário criado, por **cada** parcela criada da série e por planejado conciliado (incluindo a conciliação da RN-046), com status/valor anteriores nas conciliações
- [x] Parcela pré-existente conciliada pela RN-046 é **restaurada** no undo, nunca apagada
- [x] Undo remove os lançamentos criados sem alteração, restaura os conciliados e marca lote `revertido` / transações `revertida`
- [x] Lançamento alterado depois da importação é preservado e contado; lançamento apagado é contado como `ja_removido`
- [x] Parcela futura que só passou de `Pendente` para `Atrasado` (RF-05) é removida normalmente; parcela futura paga à mão é preservada
- [x] Transação com efeito preservado continua `confirmada` (dedup protege o que ficou); as demais viram `revertida` e o mesmo documento reimportado não é marcado `duplicada`
- [x] Undo de lote não confirmado, já revertido ou sem diário (confirmado antes do CR) → 409
- [x] Regras aprendidas (CR-054) permanecem após o undo
- [x] Tela de importação mostra "Importações anteriores" com paginação, e o diálogo de desfazer lista a prévia antes de executar
- [x] Testes existentes continuam passando (regressão) — 251 → 291 backend, 138 → 157 Vitest, todos verdes
- [x] Novos testes cobrem a mudança (backend + Vitest) — 40 em `tests/test_import_history_undo.py`, 19 Vitest (18 em `utils/importHistory.test.ts` + o caso `revertido` no `nextStageForBatch`)
- [x] Fluxo afetado exercitado em runtime antes do merge (seção 11)
- [x] Revisão de código pré-merge (`/code-review`) executada, findings registrados (seção 12)
- [x] Revisão de segurança (checklist OWASP) executada (seção 12)
- [x] Migration testada: `alembic upgrade head` + `alembic downgrade -1` em SQLite local
- [x] Documentos afetados foram atualizados (seção 5)
- [x] CI verde após o push (run 36173223541 — backend pytest + frontend tsc/eslint/vitest)

> **Regra de conclusão (CR-037):** o Status só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. Critério pendente de evento posterior (CI verde) mantém o CR "Em Implementação" até o follow-up.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco | Prob. | Impacto | Mitigação |
|---|-------|-------|---------|-----------|
| 1 | Undo apaga lançamento que o usuário editou e queria manter | Média | Alto | Assinatura do estado gravado: qualquer diferença preserva; prévia lista tudo antes de executar |
| 2 | Undo apaga lançamento **pré-existente** conciliado pela RN-046 | — (eliminado) | Alto | Diário distingue `planejado_criado` de `planejado_conciliado`; o segundo só é restaurado. Teste dedicado |
| 3 | Auto-status (RF-05) faz toda parcela vencida parecer "editada" e o undo não remove nada | Alta sem mitigação | Médio | Status normalizado na assinatura (`Pendente`≡`Atrasado`) |
| 4 | Undo libera a dedup de algo que ficou gravado → reimportar duplica | Média | Alto | Transação com efeito preservado permanece `confirmada` |
| 5 | Replicação de mês (RF-06) copia um planejado conciliado com o valor real, e o undo não alcança a réplica | Baixa | Baixo | Limitação conhecida (spec): a réplica é um lançamento do mês seguinte, criado pela transição e não pelo lote. Os planejados **criados** pela importação são `recorrente=False` e já têm as parcelas futuras criadas upfront — nada a replicar |
| 6 | Dois undos simultâneos do mesmo lote | Baixa | Baixo | `SELECT … FOR UPDATE` no lote durante o POST: o segundo espera o commit do primeiro, relê `revertido` e recebe 409 (a mitigação original — "o segundo vê `ja_removido`" — estava errada no READ COMMITTED do PostgreSQL; corrigida na revisão, finding #3) |
| 8 | Lotes dependentes desfeitos fora de ordem deixam parcela órfã em aberto | Média | Médio | 409 exigindo desfazer o mais recente antes (finding #1) |
| 9 | Banco arredonda valor com >2 casas diferente do float em memória → lançamento intocado parece editado | Baixa | Médio | `valor` arredondado no schema antes de gravar (finding #2) |
| 7 | Regra aprendida errada sobrevive ao undo | Média | Baixo | Decisão explícita; badge "aprendido" + correção no confirm seguinte |

---

## 10. Plano de Rollback

> Referência: `/docs/05-DEPLOY-GUIDE.md` (seções 4 e 5).

### 10.1 Rollback de Código

- **Método:** `git checkout -b hotfix/revert-CR-056` → `git revert -m 1 <merge>` → merge em `master` → push
- **Alternativo:** redeploy do deployment anterior no Railway
- **Commits a reverter:** o merge `--no-ff` da branch `feat/CR-056-historico-desfazer-importacao`

### 10.2 Rollback de Migration

- **Migration afetada:** `013_add_import_effects.py`
- **Comando:** `alembic downgrade 012`
- **Downgrade testado?** [x] Sim — `upgrade head` → `downgrade -1` (volta a `012`) → `upgrade head` em SQLite local (`DATABASE_URL=sqlite:///./local_cr056.db`, URL conferida antes)
- **Downgrade é destrutivo?** [x] Sim — descarta o diário de efeitos e as duas colunas de data. Nenhum dado financeiro é afetado.

### 10.3 Impacto em Dados

- **Dados perdidos no rollback?** [x] Sim — só o diário: os lotes confirmados até ali deixam de poder ser desfeitos (equivalem a lotes anteriores ao CR). Gastos, planejados e lotes ficam intactos.
- Lotes em `revertido` e transações em `revertida` continuam na tabela após o downgrade do código. O código anterior não os conhece mas não quebra: `/pending` filtra por status, e `revertida` já não contava para a dedup (que filtra por `confirmada`).
- **Backup necessário?** [ ] Sim / [x] Não — a migration só cria estrutura.

### 10.4 Rollback de Variáveis de Ambiente

- **Variáveis novas/alteradas:** Nenhuma.

### 10.5 Verificação Pós-Rollback

- [ ] Aplicação acessível e funcional
- [ ] `alembic current` mostra `012`
- [ ] Upload → revisão → confirm segue funcionando
- [ ] Usuários existentes conseguem fazer login

---

## 11. Validação Runtime

Ambiente: backend local (`uvicorn` via launcher no scratchpad) com `DATABASE_URL=sqlite:///./local_cr056.db` (migrado do zero; URL conferida no launcher com `assert`), `call_import_api` stubbada (sem `ANTHROPIC_API_KEY` local) devolvendo uma fatura com padaria, Uber, CEMIG, Netshoes 3/6 e pagamento recebido; frontend `npm run dev`; usuário local `teste.cr056@local.dev`. Rodado **duas vezes** — antes e depois das correções da revisão de código —, sempre com o banco zerado.

**HTTP** (`validate_cr056_http.py`, 14 verificações, todas ✅ na rodada final):

| # | Exercitado | Resultado |
|---|------------|-----------|
| 1 | Upload → confirm com as 4 ações (2 gastos, conciliação da Energia, série 3/6, descarte) | `{2 gastos, 4 parcelas, 1 planejado pago, 1 descartada}` |
| 2 | `GET /api/imports` | lote `confirmado`, 4 confirmadas / 1 descartada / 5 total, `pode_desfazer=true` |
| 3 | `PATCH` no gasto "Uber" (18,90 → 20,00) e prévia | `1 gasto removido, 4 parcelas removidas, 1 restaurado, 1 preservado`; nada alterado pela prévia |
| 4 | `POST /undo` | mesmos contadores da prévia |
| 5 | Estado depois | Energia volta a R$ 200,00 em aberto (**Atrasado**, porque o vencimento 15/09 já passou — RF-05 sobre o `Pendente` restaurado); só o "Uber" editado ficou nos gastos diários; nenhuma Netshoes nos 8 meses seguintes |
| 6 | Histórico depois | `revertido`, 3 revertidas + 1 confirmada (a do lançamento mantido) |
| 7 | Undo repetido / DELETE do revertido | 409 / 409 |
| 8 | Reimportar o mesmo PDF | PADARIA volta `pendente` (e chega "aprendido": a regra do CR-054 sobreviveu, como decidido); UBER segue `duplicada` (RN-052) |
| 9 | `page_size=51` / prévia de lote inexistente | 422 / 404 |
| 10 | **Lotes dependentes** (C1 cria Netshoes 3..6; C2 concilia a parcela 4 pela RN-046): undo de C1 | 409 "Desfaça antes a importação …" |
| 11 | Undo de C2 e depois de C1 | C2 restaura 1; C1 remove as 4 parcelas, 0 preservadas |

Duas falhas da **primeira** rodada foram do script, não do código: esperava `Pendente` literal (a RF-05 exibe `Atrasado` sobre o vencimento passado) e procurava a linha reimportada pelo nome original (a regra aprendida a renomeou). Script corrigido para buscar por `descricao_original`.

**Playwright** (UI, duas sessões):

- Aba Importar → seção "Importações anteriores" com os lotes, status ("Confirmado"/"Desfeito") e contadores ("2 lançadas · 2 descartadas · 1 duplicada").
- "Desfazer" → diálogo com a prévia agrupada: "Será removido (1) — Padaria Stella · Gasto diário · 03/09/2026 · R$ 23,50" e "Será restaurado (1) — Energia elétrica · volta para Atrasado · R$ 200,00" (screenshot `.playwright-mcp/cr056-undo-preview.png`). Confirmado → aviso "Importação desfeita: 1 gasto diário removido · 1 planejado restaurado.", linha virou "Desfeito" sem botão; em Gastos Planejados a Energia apareceu com R$ 200,00 (cache invalidado) e o Dashboard ganhou o badge do alerta de atraso.
- Depois das correções: "Desfazer" no lote mais antigo de um par dependente → diálogo mostra "Desfaça antes a importação "fatura-setembro.pdf"…" com o botão de executar desabilitado. Desfeito setembro (prévia: "Netshoes · Parcela 4 de 6 · volta para Pendente"), a prévia de agosto passou a listar as 4 parcelas para remoção e o undo as removeu.
- Console: **0 warnings**. Erros apenas de rede esperados: dois 401 em `/users/me` do token antigo guardado no browser (o banco local foi recriado — comportamento pré-existente da tela de login) e as respostas 409 da prévia no caminho de erro testado. O 409 aparecia em dobro por causa do `retry: 1` global — corrigido com `retry: false` na prévia (a repetição só atrasava a mensagem).

Encerramento: servidores derrubados e `local_cr056.db` removido.

---

## 12. Revisão de Código e Segurança

### 12.1 Revisão de código (`/code-review high` na branch)

10 findings: **8 corrigidos**, 2 justificados.

| # | Finding | Tratamento |
|---|---------|-----------|
| 1 | Lote B concilia parcela criada por A; desfazer A e depois B deixa a parcela órfã e em aberto | **Corrigido:** `undo_blocker_dependencies` → 409 exigindo desfazer o mais recente antes. 2 testes + cenário HTTP/Playwright |
| 2 | Assinatura do confirm usa o float em memória, o undo relê o valor arredondado pelo banco — com >2 casas divergem no PostgreSQL | **Corrigido:** `ImportConfirmDecision.valor` arredondado a 2 casas antes de gravar (0 → 422). 2 testes |
| 3 | Undo sem lock: dois POST simultâneos executam o mesmo plano; o risco #6 do CR dizia o contrário | **Corrigido:** `SELECT … FOR UPDATE` no POST; risco #6 reescrito |
| 4 | Lote pendente com `expense_id_sugerido` para planejado removido pelo undo recebe 404 no confirm | **Justificado:** mesmo comportamento que já existe quando o usuário apaga o planejado à mão; o 404 aparece na revisão e o usuário troca a ação da linha. Follow-up registrado na spec |
| 5 | Transações `revertida` mantêm os IDs de auditoria apontando para lançamentos removidos | **Justificado:** são histórico do que o confirm fez; o status `revertida` é o discriminador e nenhum código segue esses IDs. Apagá-los perderia a trilha |
| 6 | `useConfirmImport` não invalida projeção/score, e a lista de invalidação era duplicada à mão no undo | **Corrigido:** `invalidateImportedData` compartilhado; o confirm passa a invalidar projeção e score (as séries criadas deixavam essas telas desatualizadas por até 5 min) |
| 7 | Undo que falha (409 de outra aba) não recarrega o histórico | **Corrigido:** `onError` invalida o histórico e fechar o diálogo recarrega a lista |
| 8 | Aviso "todos alterados ou apagados" falso para lote confirmado sem efeitos (tudo descartado) | **Corrigido:** `undoEmptyMessage` distingue os dois casos. 3 testes |
| 9 | Lote em revisão com duplicadas mostrava só as duplicadas, sem o total extraído | **Corrigido:** total primeiro + duplicadas. 1 teste |
| 10 | `SeriesEffects.criadas` e o contador retornado eram duas fontes da mesma informação | **Corrigido:** uma lista só (`novas`); contagem = `len(novas)`, retorno inalterado para o cadastro manual |

Achado da validação runtime, fora da revisão: prévia repetida pelo `retry` global em 409 → `retry: false`.

### 12.2 Segurança (checklist OWASP do CLAUDE.md)

| Item | Resultado |
|------|-----------|
| Segredos hardcoded | OK — nenhum |
| Inputs validados via Pydantic | OK — `page >= 1`, `1 <= page_size <= 50` (Query), `valor` arredondado e > 0; `batch_id` só é usado em lookup filtrado por usuário |
| Tokens fora do `localStorage` | N/A — sem mudança de auth |
| Ownership | OK — os 3 endpoints resolvem o lote por `get_import_batch_by_id(…, user_id)` (404 para lote alheio, testado); o plano busca os lançamentos **sempre** filtrados pelo dono do lote (efeito apontando para dado alheio é tratado como ausente — testado); contagem do histórico e busca de lote dependente filtram por `user_id` |
| Queries ORM parametrizadas | OK — `IN` via ORM, em fatias de 500; sem SQL cru |
| CORS / headers | Sem mudança |
| Novas dependências | Nenhuma (backend e frontend) |
| DoS | Histórico limitado a 50 por página; o undo é limitado ao tamanho do lote (teto de 120 parcelas por série já existente) |
| Divulgação de informação | A mensagem de dependência cita o `filename` de outro lote **do próprio usuário** |

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-09-25 | Claude | CR criado. Decisões do autor: E-D dividido em dois CRs (este + CR-057 reconciliação), diário de efeitos em vez das colunas propostas no roadmap, regras aprendidas não revertidas |
| 2026-09-25 | Claude | Implementação: backend (migration 013, `import_undo.py`, 3 endpoints) e frontend (`ImportHistory`, `ImportUndoDialog`) |
| 2026-09-25 | Claude | Revisão de código: 10 findings, 8 corrigidos, 2 justificados (§12.1) — inclui ordem inversa entre lotes dependentes, arredondamento do `valor` e lock do undo |
| 2026-09-25 | Claude | Validação runtime HTTP + Playwright (§11) e revisão de segurança (§12.2). Docs sincronizados. Status segue "Em Implementação" até o CI verde |
| 2026-09-25 | Claude | Merge em master, CI verde (run 36173223541) — status: ✅ Concluído |
