# Spec — Score de Saúde Financeira (F04, CR-026)

> Extraído de `docs/03-SPEC.md` no CR-038 (conteúdo original preservado). Índice: [03-SPEC.md](../03-SPEC.md)

## F04: Score de Saude Financeira (CR-026)

### Endpoints

#### `GET /api/score`

Calcula o score de saude financeira do mes atual do usuario autenticado.

- **Auth:** Bearer token (get_current_user)
- **Response:** `HealthScoreResponse`
- **Logica:** Busca dados via CRUD existente (expenses, incomes, daily_expenses, installments) → `calculate_health_score()` → `generate_actions()` → `calculate_conservative_score()` → busca variacao_mes_anterior via score_historico → upsert score_historico → retorna response

#### `GET /api/score/history?months=12`

Retorna historico de scores dos ultimos N meses.

- **Auth:** Bearer token (get_current_user)
- **Query params:** `months` (int, ge=1, le=24, default=12)
- **Response:** `ScoreHistoryResponse`

### Calculo do Score (health_score.py)

Score deterministico 0-100, soma de 4 dimensoes (0-25 cada):

**D1 — Comprometimento Fixo (25pts):**
- Faixas de % comprometimento da renda: ≤50%=25, 50.1-60%=20, 60.1-70%=12, 70.1-80%=5, >80%=0

**D2 — Pressao de Parcelas (25pts):**
- D2a: % renda comprometida com parcelas (0-10)
- D2b: quantidade de parcelas ativas (0-5)
- D2c: penalidade por parcelas pendentes 0/Y (-5)
- D2d: bonus por parcelas encerrando em 3 meses (+5)
- Clamped 0-25

**D3 — Capacidade de Poupanca (25pts):**
- Calcula saldo livre = renda - fixos - media_variaveis
- Faixas de % livre da renda: >30%=25, 20-30%=20, 10-20%=12, 0-10%=5, negativo=0

**D4 — Comportamento/Disciplina (25pts):**
- D4a: pontualidade de pagamentos (0-10)
- D4b: consistencia de registro de gastos diarios (0-5)
- D4c: tendencia vs mes anterior (0-5)
- D4d: disciplina em novos parcelamentos (0-5)

**Edge cases:** renda=0 → score 0 + mensagem; sem despesas → score 100; primeiro mes → D4c=3.

**Classificacao:**
| Faixa | Classificacao | Cor |
|-------|--------------|-----|
| 0-25 | Critica | #EF4444 |
| 26-45 | Atencao | #F59E0B |
| 46-65 | Estavel | #3B82F6 |
| 66-85 | Saudavel | #10B981 |
| 86-100 | Excelente | #059669 |

### Cenario Conservador

- Recalcula D1+D2 com parcelas pendentes (0/Y) tratadas como ativas
- Retorna None se nao ha pendentes

### Acoes Sugeridas

- Identifica dimensoes com menor pontuacao relativa
- Gera ate 3 acoes especificas ordenadas por impacto estimado
- Cada acao inclui tipo, descricao e impacto_estimado em pontos

### Persistencia

- Tabela `score_historico` com upsert-on-read (INSERT ON CONFLICT UPDATE)
- UniqueConstraint (user_id, mes_referencia)
- `dados_snapshot` como Text (JSON string) para compatibilidade SQLite

### Schemas (schemas.py)

- HealthScoreResponse, ScoreInfo, ScoreDimensionD1-D4, ScoreDimensoes
- D2SubfactorDetail, D4SubfactorDetail, D2SubfactorsGroup, D4SubfactorsGroup
- ConservativeScenario, ConservativePendingItem, ScoreAction
- ScoreHistoryItem, ScoreHistoryResponse

### Componentes Frontend

- **ScoreGauge:** SVG circular gauge, modos compact (dashboard) e expanded (detalhe). Click no compact navega para /score
- **ScoreDimensionBreakdown:** 4 barras horizontais D1-D4, X/25, cor por ratio (verde >60%, amarelo 40-60%, vermelho <40%)
- **ScoreHistoryChart:** recharts LineChart com 5 ReferenceArea zones coloridas, tooltips com breakdown
- **ScoreActions:** cards com icones por tipo, badge de impacto estimado
- **ScoreConservativeNote:** banner amber com score atual vs conservador, lista de parcelas pendentes
- **ScoreDetailView:** pagina /score com gauge expandido, breakdown, cenario conservador, acoes, historico
- **Hook:** useHealthScore (2 queries: score + history, queryKey com user?.id)

### Regras de Negocio

- RN-S01: Score e deterministico — mesmos dados de entrada produzem mesmo score
- RN-S02: Cada dimensao contribui 0-25 pontos, total 0-100
- RN-S03: Score tem aba propria no ViewSelector ("Score", 5a aba); removido do Dashboard (CR-027)
- RN-S04: Variacao mensal calculada comparando score atual com score_historico do mes anterior
- RN-S05: Cenario conservador so exibido quando ha parcelas pendentes (0/Y)

---

