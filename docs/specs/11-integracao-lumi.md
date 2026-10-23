# Spec — Integração com o Lumi (RF-22, CR-058)

> Token de integração e API própria para o Lumi, companion de voz do usuário (projeto ai-companion-esp32, CR-014 de lá). Índice: [03-SPEC.md](../03-SPEC.md)

## Visão Geral

O usuário gera no Perfil um **token de integração**, que aparece uma vez só, e o entrega ao Lumi. Com ele, o Lumi chama a **API de integração** (`/api/integration/v1`): lança gasto diário, consulta gastos por período, lê o resumo do mês, lista as despesas planejadas e muda o status delas para Pago ou Pendente. O token não abre as rotas do app, e o JWT do login não abre as de integração (RN-054, ADR-023).

## Arquivos

| Arquivo | Responsabilidade |
|---------|------------------|
| `backend/alembic/versions/015_integration_tokens.py` | Tabela `integration_tokens` |
| `backend/app/models.py` → `IntegrationToken` | ORM |
| `backend/app/auth.py` → `generate_integration_token`, `get_integration_user` | Geração e autenticação do token |
| `backend/app/crud.py` | Tokens; gastos diários por período |
| `backend/app/services.py` → `get_daily_expenses_period_summary`, `get_integration_month` | Agregações da API |
| `backend/app/routers/integration_tokens.py` | `/api/integration-tokens` (JWT) |
| `backend/app/routers/integration.py` | `/api/integration/v1/*` (token de integração) |
| `frontend/src/components/IntegrationTokens.tsx` | Seção "Integrações" do Perfil |
| `frontend/src/hooks/useIntegrationTokens.ts`, `frontend/src/services/api.ts` | Chamadas e cache (TanStack Query) |

## Token

- Formato: `mc_` + `secrets.token_urlsafe(32)` (43 caracteres depois do prefixo).
- Gravado: `token_hash` = SHA-256 hexadecimal do token inteiro (`auth.hash_token`, o mesmo do refresh token); `prefix` = 8 caracteres depois de `mc_`.
- `get_integration_user` (dependência das rotas de integração):
  1. Lê `Authorization: Bearer <token>`. Sem o cabeçalho, ou sem o prefixo `mc_` (inclusive um JWT), devolve 401 `{"detail": "Token de integração inválido"}`.
  2. Busca pelo hash com `revoked_at IS NULL` e o usuário existente; senão, devolve 401 com a mesma mensagem.
  3. Atualiza `last_used_at`, no máximo uma vez por minuto (evita uma escrita a cada chamada), e devolve o `User`.
- Horários do token (`created_at`, `last_used_at`, `revoked_at`) gravados em **UTC** (`models.utc_now`) e devolvidos com o fuso (`Z`/`+00:00`): o Perfil mostra no fuso do navegador, e a hora é a mesma no PC e no Railway (que roda em UTC).
- O token não passa no `get_current_user`: não é um JWT válido, e as rotas do app respondem 401.
- Até 5 ativos por usuário. `name` de 1 a 40 caracteres, sem espaços nas pontas.

## Gestão dos tokens (JWT)

| Método | Rota | Body | Resposta |
|--------|------|------|----------|
| `GET` | `/api/integration-tokens` | — | 200 `IntegrationTokenResponse[]`: só os ativos, do mais novo para o mais antigo |
| `POST` | `/api/integration-tokens` | `{"name": "Lumi"}` | 201 `IntegrationTokenCreated`; 409 `{"detail": "Limite de 5 tokens ativos"}` |
| `DELETE` | `/api/integration-tokens/{id}` | — | 204; 404 se não existe, é de outro usuário ou já foi revogado |

```
IntegrationTokenResponse = {id, name, prefix, created_at, last_used_at|null}
IntegrationTokenCreated  = IntegrationTokenResponse + {token}   # a única vez em que o token aparece
```

## API de integração (token de integração)

Prefixo `/api/integration/v1`. Toda rota usa `get_integration_user`. O dono é conferido em toda leitura e escrita.

**Limite de chamadas** (`rate_limit.integration_rate_limit`, dependência do router inteiro, que roda **antes** da autenticação): **60/min por token**, somando todas as rotas `/v1` (chave = SHA-256 do token, sem depender da grafia de "Bearer"), e **120/min por IP** (segura tokens inventados, que nunca contam por token). Acima disso, 429 `{"detail": "Muitas requisições: tente de novo em instantes"}`. Biblioteca `limits` (a mesma do slowapi), em memória: 1 worker, zera a cada deploy.

| Método | Rota | Entrada | Resposta |
|--------|------|---------|----------|
| `GET` | `/categories` | — | `{categorias: {categoria: [subcategorias]}, metodos_pagamento: [...]}` |
| `POST` | `/daily-expenses` | `DailyExpenseCreate` (`descricao`, `valor`, `data`, `subcategoria`, `metodo_pagamento`) | 201 `DailyExpenseResponse`. Subcategoria e forma de pagamento validadas pela mesma função da rota do app (`services.new_daily_expense`, 422). Por ser lançamento por voz: `valor` até 50.000 e `data` de 366 dias atrás até amanhã (422 fora disso) |
| `GET` | `/daily-expenses/summary` | `de`, `ate` (AAAA-MM-DD, `de ≤ ate`, até 93 dias); `categoria?`, `subcategoria?` | `{de, ate, total, quantidade, por_categoria: {nome: total}, por_subcategoria: {nome: total}}`, filtrando pela **data** do gasto. Filtro vazio é ignorado; categoria ou subcategoria que não existe dá 422 (um total zero enganaria o Lumi) |
| `GET` | `/months/{year}/{month}` | — | `IntegrationMonth` (abaixo) |
| `GET` | `/expenses/{year}/{month}` | — | `IntegrationExpense[]`, as despesas planejadas do mês por vencimento |
| `PATCH` | `/expenses/{expense_id}` | `{"status": "Pago" \| "Pendente"}` | 200 `IntegrationExpense`; 404 se não é do usuário; 422 para outro status ou outro campo. Pendente com vencimento passado volta como `Atrasado` (RF-05), que é o que o app mostra |

```
IntegrationMonth = {
  mes_referencia, total_receitas, total_despesas (planejadas), total_gastos_diarios,
  saldo_livre            # receitas − planejadas (como a Visão Mensal, RF-04)
  saldo_apos_diarios,    # receitas − planejadas − gastos diários (como o Dashboard)
  total_pago, total_pendente, total_atrasado
}
IntegrationExpense = {id, nome, valor, vencimento, status, categoria|null, subcategoria|null,
                      parcela_atual|null, parcela_total|null}
```

- **`mes_referencia` do gasto vem da data**, não do caminho: exceção à convenção do app ("`mes_referencia` derivado do path"), como na importação (RF-21). O Lumi não escolhe mês.
- **Meses** (`/months` e `/expenses`): `year` de 2000 até o ano atual + 1 e mês de 1 a 12, sem passar do mês seguinte ao atual (422). "Hoje" é a data do servidor, como no resto do app (RF-05). As duas rotas usam o `get_monthly_summary`, que gera o mês se estiver vazio (RF-06) e atualiza o status de atraso (RF-05), como abrir o mês no app. O limite evita gerar meses distantes.

## Regras de Negócio

- RN-054 (PRD): token mostrado uma vez, guardado só como hash, revogável, escopo restrito, até 5 ativos e 60/min.
- O Lumi pede a confirmação do usuário antes de gravar (CR-014 do Lumi). Aqui, as validações são as mesmas do app.

## Frontend — seção "Integrações" do Perfil

- Lista: nome, `mc_<prefix>…`, "criado em", "último uso" (ou "nunca usado") e "Revogar", com o `ConfirmDialog` do app (botão "Revogar", pelo `confirmLabel` opcional, que tem "Excluir" como padrão). A lista busca de novo toda vez que o Perfil abre (`staleTime: 0`), porque o "último uso" muda fora da tela.
- "Gerar token para o Lumi": campo de nome (padrão "Lumi") e o botão. O token criado aparece num quadro com "Copiar" e o aviso "Guarde agora: ele não aparece de novo". Fechar o quadro some com o token da memória da página; revogar esse mesmo token também o tira da tela. A confirmação de revogar fecha antes da chamada (um segundo clique não manda outro pedido).
- Sem tokens: "Nenhuma integração ativa." Com 5 ativos, o botão fica desabilitado, com o motivo.
- O token nunca vai para o `localStorage`.

## Casos de Borda

| # | Cenário | Esperado |
|---|---------|----------|
| 1 | JWT do login numa rota de integração | 401 |
| 2 | Token de integração numa rota do app (`/api/months/...`) | 401 |
| 3 | Token revogado | 401 na hora |
| 4 | Token de outro usuário tentando a despesa de A | 404 |
| 5 | 61ª chamada no mesmo minuto, somando as rotas | 429 |
| 5b | 121 chamadas com tokens inventados do mesmo IP | 401 nas primeiras 120, 429 depois |
| 6 | Gasto com data de outro mês | `mes_referencia` = mês da data |
| 7 | Subcategoria fora da lista | 422 |
| 8 | Resumo com `de > ate` ou mais de 93 dias | 422 |
| 9 | Mês além do seguinte ao atual | 422, sem gerar dados |
| 10 | `PATCH` com `valor` ou `nome` | 422 (só `status`) |
| 11 | Sexto token ativo | 409 |
| 12 | Usuário apagado | Tokens apagados (CASCADE); o token dá 401 |
| 13 | Ano 10000 | 422 (não 500) |
| 14 | Filtro `categoria=Alimentacao` (sem acento) | 422 |
| 15 | Gasto de R$ 50.000,01 ou com data de depois de amanhã | 422 |
| 16 | Desmarcar uma conta vencida | Responde `Atrasado` |

## Testes

- `tests/test_integration_tokens.py`: criar (formato, hash, aparece uma vez), listar (só ativos, sem o token), revogar (204, 404 de outro usuário ou repetido), limite de 5, dono.
- `tests/test_integration_api.py`: autenticação (válido, revogado, JWT recusado, token recusado nas rotas do app, sem cabeçalho), cada rota do contrato, validações, dono, `last_used_at`, limite de chamadas.
- Vitest: `utils/integrationTokens.test.ts` (data e hora no fuso, rótulos, limite), `services/api.test.ts` (rotas) e `components/IntegrationTokens.test.tsx` (lista, token mostrado uma vez, revogar uma vez só, token revogado sai da tela, limite), com `react-dom` + `act` (o projeto não tem Testing Library).

## Referências

- CR-058 (este), ADR-023, RF-22, RN-054, US-31.
- Lumi: `docs/changes/CR-014-meu-controle.md` no repositório ai-companion-esp32.
