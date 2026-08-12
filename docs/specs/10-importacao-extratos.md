# Spec — Importação de Extratos e Faturas em PDF (F07, CR-046/CR-047)

**PRD Ref:** RF-21, US-29, RN-038..RN-043

## Visão Geral

O usuário faz upload do PDF de um extrato de conta ou fatura de cartão (Nubank, Itaú, Mercado Pago — sem parser fixo por banco). A IA (API Claude, leitura nativa de PDF) extrai as transações e sugere a classificação de cada uma. O resultado fica em **staging** até o usuário revisar e confirmar; só então o sistema cria gastos diários e/ou atualiza gastos planejados. CR-046 entrega o backend; CR-047 entrega a UI.

## Endpoints

Todos exigem autenticação (Bearer) e verificam ownership (404 para recurso de outro usuário).

| Endpoint | Verbo | Status | Descrição |
|----------|-------|--------|-----------|
| `/api/imports` | POST (multipart `file`) | 201 | Valida o PDF, chama a IA, grava lote `pendente_revisao` e retorna lote + transações. Rate limit **5/min** (slowapi). |
| `/api/imports/pending` | GET | 200 | Lista lotes `pendente_revisao` do usuário (retomada da revisão). |
| `/api/imports/{batch_id}` | GET | 200 | Lote + transações. |
| `/api/imports/{batch_id}/confirm` | POST | 200 | Aplica as decisões revisadas; retorna contadores do resultado. |
| `/api/imports/{batch_id}` | DELETE | 204 | Descarta lote (status → `descartado`). |

### POST /api/imports — validações de upload

- Extensão `.pdf` **e** magic bytes `%PDF-` (leitura dos primeiros bytes); caso contrário **422**
- Tamanho máximo **10MB**; caso contrário **413**
- Arquivo processado **em memória** e descartado após a chamada à IA (RN-043) — nunca escrito em disco, banco ou logs
- Feature indisponível (`IMPORT_ENABLED=false` ou `ANTHROPIC_API_KEY` ausente) → **200** com `status="indisponivel"` + reason (padrão F06, nunca 5xx)
- Erro na IA (timeout, JSON inválido após retries) → **200** com `status="erro"` + reason; nenhum lote é persistido

### Resposta do upload / GET do lote

```json
{
  "status": "disponivel",
  "batch": {
    "id": "...", "filename": "fatura-nubank-jul.pdf",
    "banco_detectado": "Nubank", "tipo_documento": "fatura",
    "status": "pendente_revisao", "created_at": "...",
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
- Transações do lote ausentes do payload são tratadas como `descartar`
- `criar_gasto_diario`: valida par categoria+subcategoria (subcategoria deve pertencer à categoria informada — não deriva só da subcategoria, por causa de subcategorias repetidas) e método de pagamento; `mes_referencia = date(data.year, data.month, 1)` (RN-039)
- `atualizar_planejado`: `expense_id` obrigatório; Expense do usuário (404 se não); status → `Pago`, valor → valor informado (RN-040)
- Auditoria: transação confirmada grava `daily_expense_id_criado` ou `expense_id_atualizado`; status da transação → `confirmada`/`descartada`; lote → `confirmado`
- Resposta: `{ "gastos_diarios_criados": N, "planejados_atualizados": N, "descartadas": N }`

## Arquitetura

```
routers/imports.py  →  import_service.py  →  API Anthropic (PDF document block)
        │                     │
        │                     └─ prompts/import_extraction_{system,user}.txt
        └─ crud.py (batches/transactions)  →  models: ImportBatch, ImportTransaction
```

- `import_service.py`:
  - `normalize_description(texto)` — lowercase, espaços colapsados, trim
  - `compute_fingerprint(user_id, data, valor, descricao)` — sha256 de `user_id|YYYY-MM-DD|valor 2 casas|descricao normalizada`
  - `build_import_prompts(db, user_id)` — interpola no template: categorias/subcategorias válidas (`categories.py`), métodos de pagamento, lista de gastos planejados Pendente/Atrasado do usuário (id, nome, valor, vencimento, mês)
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

## Persistência (migration 009)

**`import_batches`** — id (uuid str), user_id (FK CASCADE), filename, banco_detectado, tipo_documento (`extrato|fatura`), status (`pendente_revisao|confirmado|descartado`), tokens_input/output, modelo, tempo_processamento_ms, created_at, updated_at. Índice `(user_id, status)`.

**`import_transactions`** — id, batch_id (FK CASCADE), user_id (FK CASCADE), data, descricao, valor Numeric(10,2), classificacao (`gasto_diario|match_planejado|ignorar`), motivo_ignorar, expense_id_sugerido, categoria, subcategoria, metodo_pagamento, fingerprint (sha256 hex, 64), status (`pendente|confirmada|descartada|duplicada`), daily_expense_id_criado, expense_id_atualizado, created_at, updated_at. Índice `(user_id, fingerprint)`.

Sem alteração nas tabelas existentes.

## Variáveis de Ambiente

| Variável | Default | Uso |
|----------|---------|-----|
| `IMPORT_ENABLED` | `true` | Feature flag do módulo |
| `IMPORT_TIMEOUT_SECONDS` | `90` | Timeout da chamada à IA (PDFs demoram mais que a análise F06) |
| `ANTHROPIC_API_KEY` | — | Obrigatória (compartilhada com F06) |
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | Compartilhada com F06 |

## Testes

`backend/tests/test_imports.py` — API Anthropic sempre mockada:
- Upload feliz: 201, lote `pendente_revisao`, transações classificadas
- Upload não-PDF → 422; >10MB → 413; flag off / sem API key → `indisponivel`; erro da IA → `erro` sem lote
- Dedup: segunda importação com fingerprint confirmado → `duplicada`
- Confirm: cria DailyExpense no mês da data da compra, atualiza Expense (Pago + valor), auditoria gravada, contadores corretos
- Confirm inválido: categoria/subcategoria incompatíveis → 422; lote já confirmado → 409; expense de outro usuário → 404
- Ownership: get/confirm/delete de lote de outro usuário → 404
- PDF não persistido (nenhum arquivo escrito)

## Frontend (CR-047 — resumo; detalhar no CR)

- Rota `/import` (ProtectedRoute) + aba "Importar" no ViewSelector
- Stepper: upload (drag&drop) → processando → revisão (grupos: novos gastos / matches / ignoradas / duplicadas, edição inline) → resultado
- `services/api.ts`: caminho para `FormData` (sem Content-Type manual, mantendo refresh-401)
- `hooks/useImports.ts`: mutations de upload/confirm/delete + query de pending; confirm invalida `daily-expenses-summary` e queries de expenses

## Referências

- CR-046 (backend), CR-047 (frontend), plano de brainstorming 2026-08-12
- Padrões reutilizados de F06: `docs/specs/09-analise-ia.md`, `backend/app/ai_analysis.py`
