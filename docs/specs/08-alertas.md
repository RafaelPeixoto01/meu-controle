# Spec — Alertas e Notificações Inteligentes (F05, CR-033)

> Extraído de `docs/03-SPEC.md` no CR-038 (conteúdo original preservado). Índice: [03-SPEC.md](../03-SPEC.md)

### Feature: [F05] Alertas e Notificacoes Inteligentes (CR-033)

#### Descricao

Sistema de alertas inteligentes in-app que transforma o MeuControle de passivo para proativo. O motor de alertas e on-demand (calcula quando o usuario acessa o app), extensivel (cada tipo e um checker independente), e o estado dos alertas (ativo/visto/dispensado/resolvido) e persistido. 8 tipos de alertas consomem dados de todas as features: despesas planejadas (F01), Dashboard (F02), projecao de parcelas (F03), score (F04) e analise IA (F06).

#### Catalogo de Alertas (A1-A8)

| ID | Nome | Gatilho | Severidade | Dados consumidos |
|----|------|---------|------------|------------------|
| A1 | Vencimento proximo | Despesa pendente vence em X dias (config: 1/3/5/7, default: 3) | Atencao | Despesas planejadas (vencimento, status) |
| A2 | Despesa atrasada | Despesa com vencimento < hoje E status != "Pago" | Critico | Despesas planejadas (vencimento, status) |
| A3 | Parcela encerrando | Parcela nas ultimas 2 prestacoes (atual >= total-1) | Informativo | Parcelas (F03) |
| A4 | Score deteriorando | Score atual < score mes anterior em >= 5 pontos | Atencao | Score historico (F04) |
| A5 | Comprometimento alto | % comprometimento fixos > limiar (default: 50%) | Atencao | Despesas planejadas + Receitas |
| A6 | Parcela pendente ativada | Parcela muda de "0 de Y" para "1 de Y" | Critico | Parcelas (F03) |
| A7 | Alerta da analise IA | Alertas no JSON da F06 (critico/atencao/informativo) | Varia | analise_financeira.resultado.alertas |
| A8 | Gasto recorrente disfarcado | Analise IA detecta variavel que aparece todo mes | Informativo | analise_financeira.resultado.gastos_recorrentes_disfarcados |

#### Ciclo de Vida do Alerta

```
Gerado → Ativo → Visto → Dispensado
                → Resolvido (automatico)
```

| Status | Badge conta? | Aparece no card? | Aparece no banner? |
|--------|-------------|-----------------|-------------------|
| Ativo | Sim | Sim | Sim |
| Visto | Nao | Sim (sem destaque) | Nao |
| Resolvido | Nao | Nao | Nao |
| Dispensado | Nao | Nao | Nao |

**Resolucao automatica por tipo:**
- A1/A2: resolvido quando despesa marcada como paga
- A3: resolvido quando mes vira e parcela termina
- A4: resolvido no mes seguinte (novo calculo)
- A5: resolvido quando % cai abaixo do limiar
- A6: resolvido quando alerta e visto (informacao one-time)
- A7/A8: resolvido na proxima analise mensal

#### Pontos de Exibicao

1. **AlertsCard no Dashboard (F02):** Card com preview de 3 alertas mais urgentes, ordenados por severidade (Critico > Atencao > Informativo). Link "Ver todos (N)" abre modal com lista completa. Acoes rapidas (Marcar como pago) para A1/A2. Estado vazio: "Tudo em dia!".
2. **AlertBadge no ViewSelector:** Badge numerico sobre item "Dashboard". Vermelho se algum critico, amarelo caso contrario. Desaparece quando todos vistos/dispensados.
3. **AlertBanner inline nas abas:** Maximo 1 banner por aba, dismissable. Gastos Planejados (A1/A2), Parcelas (A3/A6), Score (A4). Background por severidade.

#### Endpoints (backend/app/routers/alerts.py)

**GET /api/alerts** — Calcula alertas on-demand e retorna lista com estado persistido.

Request: Auth required (Bearer token)

Response (`AlertasResponse`):
```json
{
  "alertas": [
    {
      "id": 1,
      "tipo": "A2",
      "severidade": "critico",
      "titulo": "Conta de luz esta atrasada",
      "descricao": "Venceu em 10/03 (8 dias atras). Valor: R$ 291,84.",
      "impacto_mensal": 291.84,
      "impacto_anual": null,
      "status": "ativo",
      "acao": {
        "tipo": "marcar_pago",
        "label": "Marcar como pago",
        "referencia_id": 42
      },
      "contexto_aba": "gastos_planejados",
      "created_at": "2026-03-18T08:00:00Z"
    }
  ],
  "resumo": {
    "total_ativos": 7,
    "criticos": 1,
    "atencao": 3,
    "informativos": 3,
    "nao_vistos": 3
  }
}
```

**PATCH /api/alerts/{id}/seen** — Marca alerta como visto.

Response: `{ "status": "visto", "visto_em": "2026-03-18T10:30:00Z" }`

**PATCH /api/alerts/{id}/dismiss** — Dispensa alerta.

Response: `{ "status": "dispensado", "dispensado_em": "2026-03-18T10:31:00Z" }`

**GET /api/alerts/config** — Retorna configuracoes de alertas do usuario.

Response (`ConfiguracaoAlertasResponse`):
```json
{
  "antecedencia_vencimento": 3,
  "alerta_atrasadas": true,
  "alerta_parcelas_encerrando": true,
  "alerta_score": true,
  "alerta_comprometimento": true,
  "limiar_comprometimento": 50,
  "alerta_parcela_ativada": true,
  "alerta_ia": true
}
```

**PUT /api/alerts/config** — Atualiza configuracoes de alertas. Body: `ConfiguracaoAlertasUpdate` (mesmo schema da response). Response: `ConfiguracaoAlertasResponse` atualizado.

#### Motor de Alertas (backend/app/alerts.py)

**AlertEngine** — Orquestrador que executa todos os checkers habilitados nas configuracoes do usuario. Cada checker implementa a interface `check(db, user_id, mes_referencia, config) -> List[AlertaOutput]`. O motor ordena os resultados por severidade (critico > atencao > informativo) e depois por data.

7 checkers registrados: VencimentoProximoChecker (A1), DespesaAtrasadaChecker (A2), ParcelaEncerrandoChecker (A3), ScoreDeteriorandoChecker (A4), ComprometimentoAltoChecker (A5), ParcelaAtivadaChecker (A6), AlertasIAChecker (A7+A8).

Para adicionar novo tipo: criar novo checker, registrar no AlertEngine, adicionar configuracao na tabela.

#### Configuracoes do Usuario

| Configuracao | Default | Opcoes | Campo |
|-------------|---------|--------|-------|
| Antecedencia vencimento (A1) | 3 dias | 1, 3, 5, 7 | antecedencia_vencimento |
| Alertar atrasadas (A2) | Ligado | Toggle | alerta_atrasadas |
| Alertar parcelas encerrando (A3) | Ligado | Toggle | alerta_parcelas_encerrando |
| Alertar variacao score (A4) | Ligado | Toggle | alerta_score |
| Alertar comprometimento alto (A5) | Ligado | Toggle | alerta_comprometimento |
| Limiar comprometimento (A5) | 50% | 40, 50, 60, 70 | limiar_comprometimento |
| Alertar parcela ativada (A6) | Ligado | Toggle | alerta_parcela_ativada |
| Alertas IA (A7/A8) | Ligado | Toggle | alerta_ia |

#### Schemas (schemas.py)

- AlertaAcao: tipo (marcar_pago/navegar/criar_planejado), label, referencia_id/destino
- AlertaOutput: id, tipo, severidade, titulo, descricao, impacto_mensal, impacto_anual, status, acao, contexto_aba, created_at
- AlertasResumo: total_ativos, criticos, atencao, informativos, nao_vistos
- AlertasResponse: alertas (List[AlertaOutput]), resumo (AlertasResumo)
- ConfiguracaoAlertasResponse: todos os campos de configuracao
- ConfiguracaoAlertasUpdate: campos de configuracao para atualizacao

#### Componentes Frontend

- **AlertItem:** Componente individual — icone severidade, titulo, descricao, acao, dismiss. Variante compacta (card) e expandida (modal)
- **AlertBadge:** Badge numerico no ViewSelector — vermelho (critico), amarelo (atencao/informativo)
- **AlertBanner:** Banner inline dismissable — background por severidade (vermelho/amarelo/azul claro)
- **AlertsCard:** Card no Dashboard — preview 3 alertas, resumo, "Ver todos (N)", estado vazio
- **AlertsModal:** Modal com lista completa de alertas, filtros por severidade
- **AlertsSettings:** Modal de configuracoes com 8 toggles + selects de limiar
- **Hook:** useAlerts (query alertas + resumo), useAlertsConfig (query + mutation config)

#### Regras de Negocio

- RN-A01: Motor de alertas e on-demand — calcula a cada acesso ao endpoint, nao usa cron/scheduler
- RN-A02: Ordenacao: Critico > Atencao > Informativo; dentro da mesma severidade, mais recente primeiro
- RN-A03: Card no Dashboard exibe maximo 3 alertas (os mais urgentes)
- RN-A04: Badge conta apenas alertas com status "ativo" (nao vistos/dispensados/resolvidos)
- RN-A05: Banner inline maximo 1 por aba, o mais severo/relevante
- RN-A06: Resolucao automatica: cada tipo tem regra especifica de auto-resolucao
- RN-A07: Alertas IA (A7/A8) sao promovidos do JSON da analise financeira mensal (F06)
- RN-A08: Configuracoes do usuario respeitadas — checkers desabilitados nao geram alertas
- RN-S06: Acoes ordenadas por impacto_estimado decrescente, maximo 3
