# Spec — Análise Financeira por IA (F06, CR-032)

> Criada no CR-041 a partir do CR-032 (que nunca ganhou seção no SPEC — lacuna registrada no CR-038 §8.1). Reflete a **implementação real**, que divergiu dos caminhos estimados no CR-032. Índice: [03-SPEC.md](../03-SPEC.md)

## Visão Geral

Análise financeira mensal gerada pela API Claude (Anthropic), integrada à aba Score. Analisa o **mês anterior** (mês fechado), com cache mensal persistido e graceful degradation quando a IA está indisponível ou desabilitada.

## Endpoint

| Método | Rota | Auth | Response | Observações |
|--------|------|------|----------|-------------|
| `GET`  | `/api/analysis` | Sim | `AiAnalysisResponse` | Retorna análise persistida do mês anterior; gera on-demand se não existir e houver dados suficientes |

## Arquitetura (implementação real)

| Arquivo | Responsabilidade |
|---------|------------------|
| `backend/app/ai_analysis.py` | Módulo único: coletor de dados (agrega F01/F03/F04 do mês anterior), montador de prompt (injeta nos templates), cliente Anthropic (timeout, parsing/validação do JSON), merger de ações F04+IA |
| `backend/app/routers/ai_analysis.py` | Router `GET /api/analysis` (auth required; checa `AI_ANALYSIS_ENABLED` e `ANTHROPIC_API_KEY`) |
| `backend/prompts/financial_analysis_system.txt` | System prompt (texto fixo) |
| `backend/prompts/financial_analysis_user.txt` | User prompt template com placeholders |
| `backend/app/models.py` → `AnaliseFinanceira` | ORM; tabela `analise_financeira` (migration `007_add_analise_financeira.py`) |
| `backend/app/crud.py` | Persistência/leitura da análise |
| `frontend/src/hooks/useAiAnalysis.ts` | Hook TanStack Query |
| `frontend/src/components/analysis/` | DiagnosticoCard, AlertasList, BonsComportamentos, MetasSugeridas, GastosRecorrentes, MensagemMotivacional, AnalysisPlaceholder, AnalysisFooter |
| `frontend/src/pages/ScoreDetailView.tsx` | Layout intercalado: seções do score (F04, instantâneas) + seções da IA (com skeleton loading) |

## Regras de Negócio

- **RN-IA-01 — Mês fechado:** a análise é sempre do mês anterior (acessa em abril → analisa março), garantindo dados completos.
- **RN-IA-02 — Dados mínimos:** ≥ 7 dias de gastos diários registrados OU ≥ 5 despesas planejadas no mês analisado; caso contrário, exibe "dados insuficientes" sem chamar a API.
- **RN-IA-03 — Cache mensal:** se já existe análise persistida para o mês (UNIQUE `mes_referencia`+`tipo`), retorna a salva — 1 chamada de API por mês por usuário.
- **RN-IA-04 — Mesclagem:** recomendações da IA são mescladas com as ações determinísticas do score (F04), com deduplicação (ver CR-032 §8).
- **RN-IA-05 — Graceful degradation:** com `AI_ANALYSIS_ENABLED=false` ou `ANTHROPIC_API_KEY` ausente ou erro/timeout da API, a aba Score funciona normalmente só com o conteúdo determinístico (F04) + placeholder.
- **RN-IA-06 — Consumo pela F05:** alertas do JSON da análise (severidade critico/atencao/informativo) são promovidos aos alertas A7/A8 (ver [08-alertas.md](08-alertas.md)).

## Persistência

Tabela `analise_financeira`: `mes_referencia`, `tipo` ('mensal'), `score_referencia`, `dados_input` (JSON), `resultado` (JSON), `tokens_input/output`, `modelo`, `tempo_processamento_ms`, `created_at`. UNIQUE(`mes_referencia`,`tipo`) por usuário.

## Variáveis de Ambiente

`ANTHROPIC_API_KEY` (obrigatória p/ feature), `AI_ANALYSIS_ENABLED`, `CLAUDE_MODEL` (default `claude-sonnet-4-20250514`), `AI_ANALYSIS_TIMEOUT_SECONDS` (default 30). Ver `backend/.env.example`.

## Testes

`backend/tests/test_ai_analysis.py` — coletor, montagem de prompt, parsing/validação, merger (cliente Anthropic mockado).

## Referências

- Detalhamento completo (prompts, limites de campos, layout da tela, pseudocódigo de deduplicação): [changes/CR-032-analise-financeira-ia.md](../changes/CR-032-analise-financeira-ia.md)
