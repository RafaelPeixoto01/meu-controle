# Spec — Dashboard Visual (F02, CR-019)

> Extraído de `docs/03-SPEC.md` no CR-038 (conteúdo original preservado). Índice: [03-SPEC.md](../03-SPEC.md)

## Dashboard Visual (CR-019)

### Endpoint

**GET /api/dashboard/{year}/{month}** — Retorna dados agregados para o dashboard.

Requer autenticacao JWT. Dados filtrados por `user_id`.

### Response Schema — DashboardResponse

| Campo | Tipo | Descricao |
|-------|------|-----------|
| mes_referencia | date | Primeiro dia do mes |
| total_receitas | float | Soma de todas as receitas |
| total_despesas_planejadas | float | Soma de despesas planejadas |
| total_gastos_diarios | float | Soma de gastos diarios |
| total_despesas_geral | float | Planejadas + diarios |
| saldo_livre | float | Receitas - geral |
| percentual_comprometimento | float | (geral / receitas) * 100 |
| total_parcelas_futuras | float | Valor restante de parcelas ativas |
| total_pago | float | Despesas planejadas pagas |
| total_pendente | float | Despesas planejadas pendentes |
| total_atrasado | float | Despesas planejadas atrasadas |
| categorias_planejadas | list[CategoryBreakdown] | Breakdown por categoria (planejadas) |
| categorias_diarios | list[CategoryBreakdown] | Breakdown por categoria (diarios) |
| evolucao | list[MonthEvolutionPoint] | Evolucao 6 meses |

**CategoryBreakdown:** `{ categoria: str, total: float, percentual: float, count: int }`

**MonthEvolutionPoint:** `{ mes_referencia: date, total_despesas: float, total_receitas: float, total_gastos_diarios: float, saldo_livre: float }`

### Regras de Negocio

- RN-D01: Despesas planejadas e gastos diarios sao separados nos graficos (donut charts distintos)
- RN-D02: KPIs: Saldo Livre, % Comprometimento, Gastos Planejados, Gastos Diarios
- RN-D03: Evolucao mensal mostra 6 meses (atual + 5 anteriores) com 3 series separadas
- RN-D04: Meses historicos usam queries agregadas (SUM) sem triggering de auto-generate (RF-06)
- RN-D05: Despesas sem categoria (pre-CR-016) sao agrupadas como "Outros"
- RN-D06: Divisao por zero evitada quando receita = 0 (comprometimento = 0)
- RN-D07: Status breakdown aplica-se apenas a despesas planejadas (diarios nao tem status)

### Frontend

- Dashboard e a primeira tab no ViewSelector
- Rota: `/dashboard` (protegida)
- Componentes: KeyIndicators, CategoryDonutChart (reutilizavel), EvolutionBarChart, StatusBreakdown
- Biblioteca de graficos: recharts (SVG, React nativo)
- Layout responsivo: 2 colunas desktop, empilhado mobile

---

