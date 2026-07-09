# Spec — Projeção de Parcelas (F03, CR-021)

> Extraído de `docs/03-SPEC.md` no CR-038 (conteúdo original preservado). Índice: [03-SPEC.md](../03-SPEC.md)

## Projecao de Parcelas — Visao Consolidada (CR-021, F03)

### Endpoint

**GET /api/expenses/installments/projection?months=12** — Retorna projecao de parcelas futuras com KPIs e dados mensais.

Requer autenticacao JWT. Dados filtrados por `user_id`. Parametro `months` define horizonte de projecao (default: 12, max: 24).

### Response Schema — InstallmentProjectionResponse

| Campo | Tipo | Descricao |
|-------|------|-----------|
| resumo | ProjectionSummary | KPIs consolidados |
| projecao_mensal | list[MonthlyProjection] | Projecao mes a mes |
| parcelas | list[InstallmentDetail] | Lista de parcelas com detalhes |

**ProjectionSummary:**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| total_comprometido_mes_atual | float | Soma das parcelas ativas no mes atual |
| total_restante_todas_parcelas | float | Valor restante total de todas as parcelas |
| quantidade_parcelas_ativas | int | Numero de parcelas em andamento |
| proxima_a_encerrar | object | `{ descricao: str, termina_em: str }` ou null |
| liberacao_proximos_3_meses | float | Valor mensal liberado nos proximos 3 meses |
| percentual_comprometimento | float | % da renda comprometida com parcelas |

**MonthlyProjection:**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| mes | str | Formato "YYYY-MM" |
| total_comprometido | float | Soma das parcelas ativas naquele mes |
| parcelas_ativas | int | Quantidade de parcelas ativas |
| parcelas_encerrando | list[str] | Nomes das parcelas que encerram naquele mes |
| valor_liberado | float | Diferenca vs mes anterior |
| percentual_comprometimento | float | % da renda comprometida |

**InstallmentDetail:**

| Campo | Tipo | Descricao |
|-------|------|-----------|
| descricao | str | Nome da parcela |
| valor_mensal | float | Valor da parcela mensal |
| parcela_atual | int | Parcela atual (progresso) |
| parcela_total | int | Total de parcelas |
| parcelas_restantes | int | Parcelas restantes |
| mes_inicio | date ou null | Mes do 1o vencimento nao pago (CR-024) |
| termina_em | date ou null | Mes do ultimo vencimento |
| status | str | "Encerrando" ou "Ativa" |

### Regras de Negocio

- RN-P01: Projecao calculada em runtime, sem migration ou dados persistidos
- RN-P02: Todas as parcelas com restantes > 0 sao "Ativa" ou "Encerrando" (CR-023: removido status "Pendente")
- RN-P03: Parcelas nas ultimas 2 prestacoes recebem badge "Encerrando"
- RN-P04: Renda de referencia e a soma das receitas do mes atual do usuario
- RN-P05: Tabela ordenada por data de encerramento ascendente (quem termina primeiro no topo)
- RN-P06: Grafico de barras empilhadas mostra cada parcela como segmento colorido
- RN-P07: Timeline Gantt mostra inicio e fim de cada parcela com barra colorida
- RN-P08: Toggle alterna entre visualizacao de barras empilhadas e Gantt
- RN-P09: `mes_inicio` derivado do 1o vencimento nao pago; `mes_termino` derivado do ultimo vencimento no banco (CR-024)
- RN-P10: Parcela contribui na projecao apenas nos meses entre `mes_inicio` e `mes_termino` (CR-024)
- RN-P11: `parcelas_restantes` para upfront = contagem de parcelas nao pagas; para incremental = parcela_total - progresso (CR-024)

### Frontend

- Integrado na aba Parcelas (InstallmentsView), reorganizada em 3 secoes
- Secao 1 (topo): ProjectionSummaryCards — 6 KPI cards (total mensal, total restante, qtd parcelas, proxima a encerrar, liberacao 3 meses, % comprometimento com cor semaforica)
- Secao 2 (centro): ProjectionStackedChart (barras empilhadas 12 meses) + ProjectionGantt (timeline horizontal), alternados via ProjectionChartToggle
- Secao 3 (inferior): Tabela de parcelas aprimorada com coluna "Termina em", badges de status e ordenacao por encerramento
- Hook: useInstallmentProjection (TanStack Query, staleTime 5min)
- Componentes em `frontend/src/components/installments/`
- Biblioteca de graficos: recharts (reutiliza dependencia do CR-019)
- Layout responsivo: empilhado em mobile

---

