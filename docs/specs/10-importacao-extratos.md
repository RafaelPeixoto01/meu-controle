# Spec — Importação de Extratos e Faturas em PDF (F07, CR-046 backend / CR-047 frontend / CR-049 parcelamentos / CR-052 upload assíncrono)

**PRD Ref:** RF-21, US-29, RN-038..RN-048

## Visão Geral

O usuário faz upload do PDF de um extrato de conta ou fatura de cartão (Nubank, Itaú, Mercado Pago — sem parser fixo por banco). A IA (API Claude, leitura nativa de PDF) extrai as transações e sugere a classificação de cada uma. O resultado fica em **staging** até o usuário revisar e confirmar; só então o sistema cria gastos diários e/ou atualiza gastos planejados. CR-046 entrega o backend; CR-047 entrega a UI.

**CR-052:** a extração roda **fora do request** (`BackgroundTasks`). O upload responde 202 na hora com o lote em `processando` e o frontend acompanha por polling — o usuário pode fechar a página sem perder o lote.

## Endpoints

Todos exigem autenticação (Bearer) e verificam ownership (404 para recurso de outro usuário).

| Endpoint | Verbo | Status | Descrição |
|----------|-------|--------|-----------|
| `/api/imports` | POST (multipart `file`) | **202** | Valida o PDF, grava lote `processando` e agenda a extração. Responde só metadados (sem transações). Rate limit **5/min** (slowapi). |
| `/api/imports/pending` | GET | 200 | Lista lotes `pendente_revisao` **e `processando`** do usuário (retomada / acompanhamento). |
| `/api/imports/{batch_id}` | GET | 200 | Lote + transações. **Canal de polling** do processamento (CR-052); resolve lote órfão (RN-048). |
| `/api/imports/{batch_id}/confirm` | POST | 200 | Aplica as decisões revisadas; retorna contadores do resultado. |
| `/api/imports/{batch_id}` | DELETE | 204 | Descarta lote (status → `descartado`). |

### POST /api/imports — validações de upload

- Extensão `.pdf` **e** magic bytes `%PDF-` (leitura dos primeiros bytes); caso contrário **422**
- Tamanho máximo **10MB**; caso contrário **413**
- Arquivo processado **em memória** e descartado após a chamada à IA (RN-043) — nunca escrito em disco, banco ou logs
- Feature indisponível (`IMPORT_ENABLED=false` ou `ANTHROPIC_API_KEY` ausente) → **200** com `status="indisponivel"` + reason (padrão F06, nunca 5xx)
- **CR-052:** erro na IA não é mais reportado na resposta do upload — o lote vai para `status="erro"` com `erro_mensagem` e o cliente descobre pelo polling

### Ciclo de vida do lote (CR-052)

```
POST /api/imports ──> processando ──┬──> pendente_revisao ──> confirmado
     (202)                          │                   └──> descartado
                                    └──> erro   (falha da IA, nenhuma transação
                                                 identificada, ou RN-048)
```

- `POST` responde 202 com o lote em `processando` e `transacoes: []`; a extração é agendada em `BackgroundTasks`
- A task só escreve no lote se ele **ainda estiver** `processando` (`_claim_batch`) — descartar durante a extração é decisão final, tanto no sucesso quanto no erro
- Frontend faz polling do `GET` a cada 3s enquanto `processando`

### Resposta do upload / GET do lote

```json
{
  "status": "disponivel",
  "batch": {
    "id": "...", "filename": "fatura-nubank-jul.pdf",
    "banco_detectado": "Nubank", "tipo_documento": "fatura",
    "status": "pendente_revisao", "erro_mensagem": null, "created_at": "...",
    "transacoes": [
      {
        "id": "...", "data": "2026-07-28", "descricao": "PADARIA STELLA",
        "valor": 23.50, "classificacao": "gasto_diario",
        "categoria": "Alimentação", "subcategoria": "Padaria",
        "metodo_pagamento": "Cartão de Crédito",
        "expense_id_sugerido": null, "motivo_ignorar": null,
        "status": "pendente"
      },
      {
        "id": "...", "data": "2026-07-10", "descricao": "CEMIG ENERGIA",
        "valor": 187.32, "classificacao": "match_planejado",
        "expense_id_sugerido": "<uuid do Expense>", "status": "pendente"
      },
      {
        "id": "...", "data": "2026-07-05", "descricao": "PAGAMENTO RECEBIDO",
        "valor": 2500.00, "classificacao": "ignorar",
        "motivo_ignorar": "pagamento de fatura", "status": "pendente"
      }
    ]
  }
}
```

### POST /api/imports/{batch_id}/confirm — request

```json
{
  "transacoes": [
    { "id": "...", "acao": "criar_gasto_diario",
      "descricao": "Padaria Stella", "valor": 23.50, "data": "2026-07-28",
      "categoria": "Alimentação", "subcategoria": "Padaria",
      "metodo_pagamento": "Cartão de Crédito" },
    { "id": "...", "acao": "atualizar_planejado", "expense_id": "<uuid>", "valor": 187.32 },
    { "id": "...", "acao": "descartar" }
  ]
}
```

- Toda transação do payload deve pertencer ao lote; lote deve estar `pendente_revisao` (senão 409)
- Transações do lote ausentes do payload são tratadas como `descartar` — exceto as `duplicada`, que permanecem `duplicada` (auditoria consistente com o DELETE)
- Duas decisões `atualizar_planejado` apontando para o mesmo `expense_id` no mesmo confirm → 422 (evita sobrescrita silenciosa)
- `criar_gasto_diario`: valida par categoria+subcategoria (subcategoria deve pertencer à categoria informada — não deriva só da subcategoria, por causa de subcategorias repetidas) e método de pagamento; `mes_referencia = date(data.year, data.month, 1)` (RN-039)
- `criar_planejado_parcelado` (CR-049): cria a série de parcelas — ver seção "Compras parceladas" abaixo
- `atualizar_planejado`: `expense_id` obrigatório; Expense do usuário (404 se não); status → `Pago`, valor → valor informado (RN-040)
- Auditoria: transação confirmada grava `daily_expense_id_criado` ou `expense_id_atualizado`; status da transação → `confirmada`/`descartada`; lote → `confirmado`
- Resposta: `{ "gastos_diarios_criados": N, "planejados_criados": N, "planejados_atualizados": N, "descartadas": N }`

## Compras parceladas (CR-049 — item E-A do roadmap v2)

Compra parcelada identificada pela numeração explícita na descrição (`3/10`, `PARC 03/10`, `PARCELA 3 DE 10`) que **não** casou com nenhum gasto planejado existente. Se houver planejado correspondente, o prompt dá precedência ao `match_planejado` — é o que evita recriar parcelas ao importar meses consecutivos.

**Classificação `parcelamento`.** A IA devolve `parcela_atual`/`parcela_total` e a `descricao` já limpa da numeração (o nome precisa ser estável entre meses para a RN-046 casar). `_parse_parcelas` exige inteiros com `total > 1` e `1 <= atual <= total`; numeração incoerente rebaixa a transação para `gasto_diario`.

**Ação `criar_planejado_parcelado`.** Payload:

```json
{ "id": "...", "acao": "criar_planejado_parcelado",
  "descricao": "Netshoes", "valor": 149.90, "data": "2026-05-15",
  "categoria": "Compras Pessoais", "subcategoria": "Roupas",
  "parcela_atual": 3, "parcela_total": 10 }
```

- `parcela_atual`/`parcela_total` obrigatórios, entre 1 e `MAX_PARCELAS` (120), com `atual <= total` e `total >= 2` — senão 422
- **RN-045:** `data` é a data da **compra**. A parcela k vence em `add_months(data, k-1)`; a parcela informada ancora a série nesse vencimento, e `mes_referencia` é o mês dele. Uma compra de 15/05 com "03/10" cria a parcela 3 em **julho**, não em maio
- **RN-044:** a parcela informada nasce `Pago` (já cobrada nesta fatura); as seguintes, `Pendente` e `recorrente=False`
- **RN-046:** parcela já existente no mês-alvo (mesmo nome + numeração) não é recriada — a informada é conciliada (status e valor atualizados) e as futuras são puladas; nenhuma delas entra em `planejados_criados`
- Categoria é **opcional** (o modelo `Expense` permite nula), mas se vier, o par precisa ser válido. Sem fallback para o palpite da IA: limpar a categoria na revisão significa gravar sem categoria
- Duas decisões do mesmo lote apontando para a mesma série → 422 (espelha a guarda do `atualizar_planejado`)
- Auditoria: `expense_id_criado` recebe o id da parcela ancora

A criação upfront das parcelas é feita por `services.create_expense_with_installments()`, **compartilhada com o cadastro manual** ([`routers/expenses.py`](../../backend/app/routers/expenses.py)) — o import apenas passa `status_primeira=Pago` e `skip_existing=True`.

## Arquitetura

```
routers/imports.py  →  import_service.py  →  API Anthropic (PDF document block)
        │                     │
        │                     └─ prompts/import_extraction_{system,user}.txt
        └─ crud.py (batches/transactions)  →  models: ImportBatch, ImportTransaction
```

- `import_service.py`:
  - `normalize_description(texto)` — lowercase, espaços colapsados, trim
  - `compute_fingerprint(user_id, data, valor, descricao, parcela_atual=None, parcela_total=None)` — sha256 de `user_id|YYYY-MM-DD|valor 2 casas|descricao normalizada`, mais `|atual/total` quando houver parcela. Sem a numeração, parcelas da mesma compra colidiriam (mesma data de compra, mesmo valor, mesma descrição limpa) e a parcela do mês seguinte nasceria `duplicada`
  - `collect_open_expenses(db, user_id)` — gastos planejados Pendente/Atrasado dos últimos 3 meses + mês seguinte (candidatos a match; também define os `expense_id` válidos para a validação)
  - `build_import_prompts(open_expenses)` — interpola no template: categorias/subcategorias válidas (`categories.py`), métodos de pagamento e a lista de planejados em aberto (id, nome, parcela, valor, vencimento, status)
  - `process_import_batch(session_factory, batch_id, user_id, pdf_bytes)` (CR-052) — a task de background: monta o contexto, chama a IA e grava o staging. Abre a sessão em **dois trechos curtos**, com a chamada à IA entre eles, para não segurar conexão do pool em transação por minutos. `pdf_bytes` vive só na closure (RN-043)
  - `_claim_batch(db, batch_id, user_id)` (CR-052) — relê o lote e só o devolve se ainda estiver `processando`
  - `resolve_stale_batch(db, batch)` (CR-052) — RN-048; `STALE_PROCESSING_MINUTES = 30`, acima do pior caso da extração (3 tentativas do retry próprio × 3 do SDK × 180s ≈ 27 min)
  - `call_import_api(pdf_bytes, system_prompt, user_prompt)` — `client.messages.create` com content blocks `[document(base64 pdf), text(user_prompt)]`, `max_tokens=8192`, retry/backoff e `_parse_ai_json` reutilizado do padrão F06; timeout `IMPORT_TIMEOUT_SECONDS` (default 90s)
  - `validate_ai_result(resultado)` — descarta/normaliza transações malformadas (data inválida, valor <= 0, classificação desconhecida vira `gasto_diario` sem categoria → pendente de revisão); par categoria/subcategoria inválido zera os campos (usuário define na revisão)
- A IA devolve: `{"banco": str, "tipo_documento": "extrato"|"fatura", "transacoes": [{data, descricao, valor, classificacao, expense_id?, motivo_ignorar?, categoria?, subcategoria?, metodo_pagamento?}]}`
- Dedup no upload: fingerprints com status `confirmada` do usuário → transação nasce `duplicada` (RN-042)

## Regras de Negócio

| Regra | Origem |
|-------|--------|
| Staging obrigatório; nada gravado sem confirmação | RN-038 |
| Gasto diário criado no mês da data da compra | RN-039 |
| Match atualiza status Pago + valor real | RN-040 |
| Receitas/transferências/pagamento de fatura → `ignorar` (resgatáveis na revisão) | RN-041 |
| Dedup por fingerprint de transação confirmada | RN-042 |
| PDF nunca persistido | RN-043 |
| Extração assíncrona: upload responde 202 e o lote nasce `processando` | RN-047 (CR-052) |
| Lote `processando` há mais de 30 min é resolvido como `erro` na leitura | RN-048 (CR-052) |

## Persistência (migration 009)

**`import_batches`** — id (uuid str), user_id (FK CASCADE), filename, banco_detectado, tipo_documento (`extrato|fatura`), status (`processando|pendente_revisao|confirmado|descartado|erro`), **erro_mensagem** (CR-052), tokens_input/output, modelo, tempo_processamento_ms, created_at, updated_at. Índice `(user_id, status)`.

**`import_transactions`** — id, batch_id (FK CASCADE), user_id (FK CASCADE), data, descricao, valor Numeric(10,2), classificacao (`gasto_diario|match_planejado|parcelamento|ignorar`), motivo_ignorar, expense_id_sugerido, categoria, subcategoria, metodo_pagamento, **parcela_atual, parcela_total** (CR-049), fingerprint (sha256 hex, 64), status (`pendente|confirmada|descartada|duplicada`), daily_expense_id_criado, expense_id_atualizado, **expense_id_criado** (CR-049), created_at, updated_at. Índice `(user_id, fingerprint)`.

Migration **010** (CR-049) adiciona `parcela_atual`, `parcela_total` e `expense_id_criado` via `batch_alter_table`.
Migration **011** (CR-052) adiciona `erro_mensagem` em `import_batches`. Os valores novos de `status` não exigem DDL — a coluna é `String(20)` sem constraint.

Sem alteração nas tabelas existentes.

## Variáveis de Ambiente

| Variável | Default | Uso |
|----------|---------|-----|
| `IMPORT_ENABLED` | `true` | Feature flag do módulo |
| `IMPORT_TIMEOUT_SECONDS` | `180` | Timeout da chamada à IA (PDF + raciocínio; era 90 antes do CR-048) |
| `ANTHROPIC_API_KEY` | — | Obrigatória (compartilhada com F06) |
| `CLAUDE_MODEL` | `claude-opus-5` | Compartilhada com F06 (CR-048; exige modelo da geração 4.6+) |

### Parâmetros da chamada (CR-048)

| Parâmetro | Valor | Motivo |
|-----------|-------|--------|
| `model` | `DEFAULT_MODEL` (`claude-opus-5`) | Conciliação com gastos planejados é tarefa de julgamento |
| `thinking` | `{"type": "adaptive"}` | Desligar no Opus 5 pode vazar tags XML internas e quebrar o parse do JSON |
| `output_config` | `{"effort": "low"}` | Extração é mecânica; baixar o effort é a forma recomendada de conter custo/latência |
| `max_tokens` | 16000 | Cobre raciocínio + JSON de uma fatura grande (era 8192) |
| `temperature` | **ausente** | Rejeitado com 400 na geração atual |

Leitura da resposta via `extract_response_text` (compartilhada com a F06). `stop_reason == "refusal"` levanta `AiRefusalError` fora do retry — importante aqui porque cada tentativa reenviaria o PDF inteiro. Ver [ADR-019](../02-ARCHITECTURE.md).

## Testes

`backend/tests/test_imports.py` — API Anthropic sempre mockada:
- Upload feliz: **202** com lote `processando` e sem transações; depois da task, `pendente_revisao` com as transações classificadas
- Upload não-PDF → 422; >10MB → 413; flag off / sem API key → `indisponivel`
- Assíncrono (CR-052): erro da IA e documento sem transações gravam o lote em `erro` com `erro_mensagem` (sem conteúdo do documento); metadata da chamada gravada pela task; `/pending` inclui `processando`; lote descartado durante a extração não é ressuscitado (sucesso **e** erro); confirm em lote `processando` → 409; RN-048 marca `erro` acima da janela e preserva dentro dela, saindo do `/pending`
- Dedup: segunda importação com fingerprint confirmado → `duplicada`
- Confirm: cria DailyExpense no mês da data da compra, atualiza Expense (Pago + valor), auditoria gravada, contadores corretos
- Parcelamentos (CR-049): série completa com meses/vencimentos corretos a partir da data da compra, parcela âncora Paga e futuras Pendentes, RN-046 (não duplica nem a âncora nem as futuras), 422 para numeração inválida/acima do teto/série repetida no lote, fingerprint distinguindo parcelas da mesma compra
- Confirm inválido: categoria/subcategoria incompatíveis → 422; lote já confirmado → 409; expense de outro usuário → 404
- Ownership: get/confirm/delete de lote de outro usuário → 404
- PDF não persistido (nenhum arquivo escrito)

## Frontend (CR-047)

- Rota `/import` (ProtectedRoute) + aba "Importar" no ViewSelector (6ª aba)
- `pages/ImportView.tsx` — máquina de estados do fluxo: `upload` → **`processing`** → `review` → `result`. CR-052: o upload devolve 202 e a transição é dirigida pelo polling (`nextStageForBatch`); ao entrar na revisão o lote é **copiado** para o state e o polling desligado, para que nenhum refetch troque o objeto sob a `ImportReview` e descarte edições
- `components/imports/ImportUpload.tsx` — seleção de PDF com validação client-side (extensão + 10MB), estado "enviando o arquivo" (só a transferência), banner de lotes em aberto que distingue `processando` (spinner + "Acompanhar") de `pendente_revisao` ("Retomar revisão"), exibição de `indisponivel`/`erro` sem quebrar
- `components/imports/ImportProcessing.tsx` (CR-052) — tela do estágio assíncrono: "você pode fechar esta página", cancelamento do lote, e título neutro enquanto o status ainda não chegou
- `components/imports/ImportReview.tsx` — grupos (novos gastos / conciliações / **compras parceladas** / ignoradas / duplicadas), checkbox por transação (ignoradas e duplicadas nascem desmarcadas), edição inline (destino, valor, data, descrição, categoria+subcategoria em cascata, método), validação por linha antes do confirm (inclui guarda contra pagar o mesmo planejado 2x — espelho da regra do backend); conciliação mostra o planejado alvo (nome, parcela, valor, status, vencimento)
- `components/imports/ImportResult.tsx` — contadores do resultado + navegação (Gastos Diários / Planejados / importar outro)
- `utils/importReview.ts` — helpers puros testados: `groupTransactions`, `buildInitialDecisions`, `validateDecision`, `buildConfirmPayload`, `monthsToFetchForMatches`, `describeInstallmentSeries` (CR-049: prévia "cria até N parcelas … até MM/AAAA"), `nextStageForBatch` (CR-052: estágio correspondente ao status do lote)
- CR-049 na revisão: destino "Compra parcelada", campos de numeração `x/y` (máx. 120), rótulo "Data da compra" e prévia da série; `ImportResult` mostra o contador de parcelas criadas
- `hooks/useImports.ts` — `useImportBatch` (CR-052: polling de 3s enquanto `processando`, `refetchOnWindowFocus` desligado, e segue tentando enquanto não houver status conhecido para não travar o spinner numa falha de rede), `usePendingImports`, `useMatchTargets` (mapa expense_id→Expense dos meses das transações + atual/anterior), `useUploadImport`, `useConfirmImport` (invalida `imports-pending`, `daily-expenses-summary`, `monthly-summary`, `dashboard`, `installments`, `alerts`), `useDiscardImport`
- `services/api.ts`: `requestMultipart` — FormData sem Content-Type manual, Bearer token e interceptor refresh-401 com retry (erro pós-refresh expõe o `detail` do backend)

## Referências

- CR-046 (backend), CR-047 (frontend), CR-049 (compras parceladas), CR-052 (upload assíncrono — item E-B), plano de brainstorming 2026-08-12, [roadmap F07 v2](../F07-v2-roadmap-importacao.md)
- Padrões reutilizados de F06: `docs/specs/09-analise-ia.md`, `backend/app/ai_analysis.py`
