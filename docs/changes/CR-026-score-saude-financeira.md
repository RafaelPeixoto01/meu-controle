# Change Request — CR-004: Score de Saúde Financeira

**Versão:** 1.0  
**Data:** 2026-03-16  
**Status:** Concluido
**Autor:** Rafael Peixoto  
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Implementar um score de saúde financeira de 0 a 100, calculado localmente de forma determinística, com 4 dimensões ponderadas: comprometimento com fixos (25%), pressão de parcelas (25%), capacidade de poupança (25%) e comportamento/disciplina (25%). O score é exibido como card no Dashboard (F02) e possui tela dedicada com breakdown por dimensão, evolução histórica mês a mês, e ações sugeridas de maior impacto. O score é a "fonte da verdade" numérica — a análise por IA (F06, futura) receberá o score como input e agregará interpretação qualitativa, sem recalcular (Opção B).

---

## 2. Classificação

| Campo            | Valor                                                                 |
|------------------|-----------------------------------------------------------------------|
| Tipo             | Nova Feature                                                          |
| Origem           | Roadmap F04 (Benchmark competitivo + evolução do produto)             |
| Urgência         | Próxima sprint                                                        |
| Complexidade     | Média                                                                 |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

O MeuControle possui:
- Despesas planejadas com categorias (F01 implementada)
- Gastos diários com categorias (F01 implementada)
- Dashboard visual com gráficos (F02 implementada)
- Visão consolidada de parcelas futuras com projeção (F03 implementada)
- Prompt de análise financeira por IA já desenhado (não integrado), que inclui um score de 0-100 calculado pela LLM

Não existe nenhuma métrica unificada que comunique "como estou financeiramente?" de forma instantânea. O usuário precisa interpretar múltiplos gráficos, tabelas e números para chegar a uma conclusão.

### Problema ou Necessidade

1. **Ausência de diagnóstico instantâneo**: o usuário vê dados, mas não vê um veredito. Dashboards mostram o "quanto", não o "quão bem".
2. **Sem mecanismo de evolução temporal**: não há como comparar a saúde financeira de um mês com o anterior. Sem isso, o progresso é invisível.
3. **Sem gatilho para ações**: os dados existem mas não provocam ação. Um score que cai 5 pontos e explica por quê gera urgência; uma tabela que muda não gera.
4. **Preparação para F06 (Análise IA)**: quando a IA for integrada, precisa receber o score como input para contextualizar suas recomendações, não recalculá-lo (Opção B definida).

### Situação Desejada (TO-BE)

**No Dashboard (F02):**
- Card de score com gauge circular (0-100), cor semafórica, classificação textual e variação vs. mês anterior (ex: "↑ +5 pontos")
- Toque no card navega para tela de detalhe

**Na tela de detalhe do Score:**
- Gauge circular grande com nota, classificação e mensagem contextual
- Breakdown das 4 dimensões com barras horizontais ou gráfico radar
- Gráfico de evolução histórica (linha temporal dos últimos 6-12 meses)
- Seção "Como melhorar" com as 2-3 ações de maior impacto no score
- Cenário conservador: nota complementar quando existem parcelas pendentes (0 de Y), mostrando impacto potencial

**No backend:**
- Serviço de cálculo determinístico (sem IA, sem API externa)
- Persistência do score mensal com snapshot dos dados usados no cálculo
- Recálculo automático quando dados do mês mudam (despesa paga, nova parcela, etc.)

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                              | Antes (AS-IS)                                        | Depois (TO-BE)                                                                      |
|----|-----------------------------------|------------------------------------------------------|-------------------------------------------------------------------------------------|
| 1  | Métrica unificada de saúde        | Inexistente                                          | Score 0-100 calculado localmente com 4 dimensões                                    |
| 2  | Dashboard (F02)                   | Gráficos e indicadores financeiros                   | Adiciona card de score com gauge, cor e variação mensal                              |
| 3  | Histórico de evolução             | Inexistente                                          | Tabela `score_historico` com score mensal + snapshot                                 |
| 4  | Ações sugeridas                   | Inexistentes                                         | 2-3 ações derivadas das dimensões com menor pontuação                               |
| 5  | Integração com F06 (futuro)       | Prompt IA calcula score próprio                      | Prompt IA receberá score local como input (Opção B), sem recalcular                 |

### 4.2 O que NÃO muda

- Modelo de dados de despesas planejadas, gastos diários e parcelas
- Dashboard existente (F02) — o card de score é adicionado, nada removido
- Aba Parcelas (F03) — a projeção de parcelas alimenta o cálculo da D2 mas não é alterada
- Categorização (F01) — as categorias alimentam o cálculo da D3 mas não são alteradas
- Prompt de análise financeira existente (será adaptado na F06, não agora)

---

## 5. Modelo de Cálculo do Score

### Visão geral

| Dimensão | Peso | O que mede | Fonte de dados |
|----------|------|-----------|----------------|
| D1: Comprometimento com fixos | 25 pts | % da renda consumida por despesas fixas | Despesas planejadas + Receitas |
| D2: Pressão de parcelas | 25 pts | Carga e risco das parcelas ativas | Parcelas (F03) |
| D3: Capacidade de poupança | 25 pts | Quanto sobra depois de fixos e variáveis | Receitas - Fixos - Variáveis (categorias F01) |
| D4: Comportamento e disciplina | 25 pts | Pontualidade, consistência, tendência | Status de pagamento + histórico |

**Score Total = D1 + D2 + D3 + D4** (0 a 100)

### D1: Comprometimento com despesas fixas (0-25 pontos)

Calcula `percentual_fixos = (total_despesas_planejadas / renda_liquida) * 100`

| Faixa de comprometimento | Pontos |
|--------------------------|--------|
| ≤ 50% | 25 |
| 50,1% – 60% | 20 |
| 60,1% – 70% | 12 |
| 70,1% – 80% | 5 |
| > 80% | 0 |

Referência: regra 50/30/20 adaptada à realidade brasileira.

### D2: Pressão de parcelas (0-25 pontos)

Subdividida em 4 subfatores:

**D2a — % da renda só em parcelas (0-10 pontos):**

| Faixa | Pontos |
|-------|--------|
| ≤ 15% | 10 |
| 15,1% – 25% | 7 |
| 25,1% – 35% | 4 |
| 35,1% – 50% | 2 |
| > 50% | 0 |

**D2b — Quantidade de parcelas simultâneas (0-5 pontos):**

| Quantidade | Pontos |
|-----------|--------|
| ≤ 3 | 5 |
| 4 – 6 | 3 |
| 7 – 10 | 1 |
| > 10 | 0 |

**D2c — Parcelas pendentes não iniciadas (0 ou -5 pontos):**

| Condição | Pontos |
|----------|--------|
| Nenhuma parcela pendente (0 de Y) | 0 (neutro) |
| 1 ou mais parcelas pendentes | -5 (penalidade por risco oculto) |

**D2d — Alívio futuro próximo (+0 a +5 pontos bônus):**

| Condição | Pontos |
|----------|--------|
| Parcelas encerrando nos próximos 3 meses liberam ≥ 10% da renda | +5 |
| Liberam entre 5% e 10% | +3 |
| Liberam < 5% | 0 |

**D2 total = max(0, min(25, D2a + D2b + D2c + D2d))**

Nota: o total é limitado entre 0 e 25 (a penalidade de D2c pode reduzir abaixo de 0, que é clamped para 0; o bônus de D2d não ultrapassa 25).

### D3: Capacidade de poupança (0-25 pontos)

Calcula `saldo_livre_real = renda - total_fixos - media_variaveis_3_meses`

Se menos de 3 meses de histórico de gastos diários, usa: `media_variaveis = total_variáveis_mes_atual * (30 / dias_registrados)`

Calcula `percentual_livre = (saldo_livre_real / renda) * 100`

| Faixa | Pontos |
|-------|--------|
| ≥ 20% | 25 |
| 15% – 19,9% | 20 |
| 10% – 14,9% | 15 |
| 5% – 9,9% | 8 |
| 0,1% – 4,9% | 3 |
| ≤ 0% (negativo) | 0 |

**Uso de categorias (F01):** com categorias disponíveis, o diagnóstico contextual identifica as categorias que mais impactam o saldo livre. Ex: "Alimentação consome 22% da renda (benchmark saudável: 15%). Reduzir para 18% aumentaria seu score em ~4 pontos."

### D4: Comportamento e disciplina (0-25 pontos)

**D4a — Pontualidade nos pagamentos (0-10 pontos):**

`pontos = (despesas_pagas_em_dia / total_despesas_do_mes) * 10`

Arredondado para inteiro. Despesas com status "Atrasado" reduzem proporcionalmente.

**D4b — Consistência de registro de gastos diários (0-5 pontos):**

`pontos = min(5, (dias_com_registro_no_mes / 20) * 5)`

Benchmark: 20 dias de registro no mês = nota máxima (reconhece que nem todo dia tem gasto).

**D4c — Tendência mensal (0-5 pontos):**

Compara % de comprometimento do mês atual vs. mês anterior:

| Condição | Pontos |
|----------|--------|
| Comprometimento reduziu ≥ 3 p.p. | 5 |
| Comprometimento reduziu 0,1 – 2,9 p.p. | 3 |
| Comprometimento estável (variação ≤ 0,1 p.p.) | 2 |
| Comprometimento aumentou | 0 |

No primeiro mês de uso (sem histórico anterior): assume 3 pontos (neutro).

**D4d — Disciplina de parcelamento (0-5 pontos):**

| Condição | Pontos |
|----------|--------|
| Nenhuma nova parcela longa (> 12x) criada no mês | 5 |
| Nova parcela longa criada, mas < 5% da renda | 2 |
| Nova parcela longa criada, ≥ 5% da renda | 0 |

**D4 total = D4a + D4b + D4c + D4d** (0 a 25)

---

## 6. Classificação e comunicação visual

| Faixa | Classificação | Cor hex | Mensagem padrão |
|-------|---------------|---------|-----------------|
| 0-25 | Crítica | #C0392B (vermelho) | "Situação exige ação imediata" |
| 26-45 | Atenção | #E67E22 (laranja) | "Alguns pontos precisam de ajuste" |
| 46-65 | Estável | #F1C40F (amarelo) | "Caminho certo, mas há espaço para melhorar" |
| 66-85 | Saudável | #27AE60 (verde claro) | "Finanças bem organizadas" |
| 86-100 | Excelente | #1E8449 (verde escuro) | "Saúde financeira excepcional" |

A mensagem padrão é complementada por uma frase contextual derivada da dimensão de menor pontuação. Exemplos:

- D2 é a menor: "Sua principal oportunidade: reduzir a pressão de parcelas. O Empr. Sonia termina em 2 meses, o que pode melhorar seu score."
- D3 é a menor: "Seu saldo livre está apertado. Revisar gastos com Alimentação (22% da renda) pode abrir espaço."
- D4 é a menor: "Manter os pagamentos em dia é a forma mais rápida de subir o score."

---

## 7. Ações sugeridas ("Como melhorar")

A tela de detalhe exibe até 3 ações ordenadas por impacto estimado no score. Cada ação é derivada automaticamente das dimensões com menor pontuação:

| Condição | Ação sugerida | Impacto estimado |
|----------|---------------|------------------|
| D1 > 60% comprometimento | "Revisar despesas fixas não essenciais. Categorias com maior peso: [top 2 categorias]" | +X pontos se reduzir para Y% |
| D2 com parcelas pendentes | "Atenção: [nome parcela] ainda não iniciou. Quando ativar, comprometimento sobe para Z%" | Informativo (alerta) |
| D2 com parcelas encerrando | "O [nome parcela] termina em [mês]. Redirecionar R$ [valor]/mês para poupança sobe score em ~X pontos" | +X pontos |
| D3 < 10% livre | "Sua maior oportunidade: [categoria de maior gasto variável]. Reduzir de R$X para R$Y libera R$Z/mês" | +X pontos |
| D4a < 8 pontos | "Pagar [N] despesas atrasadas melhora seu score imediatamente" | +X pontos |
| D4b < 3 pontos | "Registrar gastos diários com mais frequência melhora sua visibilidade e seu score" | +X pontos |

O cálculo de "impacto estimado" é feito recalculando o score com o cenário hipotético da ação aplicada.

---

## 8. Cenário conservador (parcelas pendentes)

Quando existem parcelas com status "Pendente" (0 de Y), a tela de detalhe exibe uma nota complementar:

> **Cenário conservador:** Se todas as parcelas pendentes forem ativadas, seu score cairia de **[score_atual]** para **[score_conservador]** ([classificação_conservadora]).

O score conservador é calculado incluindo as parcelas pendentes como se estivessem ativas, usando valor mensal estimado = valor_total / total_parcelas.

---

## 9. Impacto nos Documentos

| Documento                          | Impactado? | Seções Afetadas                        | Ação Necessária                                   |
|------------------------------------|------------|----------------------------------------|---------------------------------------------------|
| `/docs/PRD.md`                     | Sim        | Requisitos Funcionais, Roadmap         | Adicionar RF para score de saúde financeira        |
| `/docs/ARCHITECTURE.md`            | Sim        | Modelagem de Dados                     | Adicionar tabela `score_historico`                 |
| `/docs/SPEC.md`                    | Sim        | Features                               | Detalhar módulo de score, endpoints, componentes UI |
| `/docs/IMPLEMENTATION_PLAN.md`     | Sim        | Adicionar novo grupo de tarefas        | Inserir tarefas da F04                             |

---

## 10. Impacto no Código

### 10.1 Arquivos Afetados

| Ação      | Caminho (estimado)                                           | Descrição                                                     |
|-----------|--------------------------------------------------------------|---------------------------------------------------------------|
| Criar     | `backend/services/health_score.py`                           | Serviço de cálculo do score: recebe dados financeiros, retorna score com breakdown por dimensão |
| Criar     | `backend/services/health_score_actions.py`                   | Gerador de ações sugeridas baseado nas dimensões de menor pontuação |
| Criar     | `backend/schemas/health_score.py`                            | Schemas Pydantic para request/response do score               |
| Criar     | `backend/routes/health_score.py`                             | Endpoints: GET /api/score (atual), GET /api/score/history (evolução) |
| Modificar | `backend/routes/__init__.py` (ou equivalente)                | Registrar novas rotas                                         |
| Criar     | `backend/models/score_historico.py`                          | Modelo SQLAlchemy/ORM para tabela score_historico              |
| Criar     | `frontend/src/components/score/ScoreGauge.tsx`               | Gauge circular com nota, cor semafórica e classificação        |
| Criar     | `frontend/src/components/score/ScoreDimensionBreakdown.tsx`  | Barras horizontais ou radar com as 4 dimensões                |
| Criar     | `frontend/src/components/score/ScoreHistoryChart.tsx`         | Gráfico de linha com evolução dos últimos 6-12 meses          |
| Criar     | `frontend/src/components/score/ScoreActions.tsx`              | Cards com ações sugeridas e impacto estimado                  |
| Criar     | `frontend/src/components/score/ScoreConservativeNote.tsx`     | Nota de cenário conservador quando há parcelas pendentes      |
| Criar     | `frontend/src/pages/ScoreDetail.tsx`                         | Tela dedicada combinando todos os componentes acima           |
| Modificar | `frontend/src/pages/Dashboard.tsx` (ou equivalente)          | Adicionar card de score (ScoreGauge compacto + variação mensal + link para detalhe) |
| Criar     | `frontend/src/hooks/useHealthScore.ts`                       | Hook para consumir endpoints de score                         |
| Criar     | `frontend/src/types/healthScore.ts`                          | Types TypeScript para score                                   |
| Criar     | `backend/tests/test_health_score.py`                         | Testes unitários do serviço de cálculo                        |
| Criar     | `backend/tests/test_health_score_actions.py`                 | Testes unitários do gerador de ações                          |

### 10.2 Banco de Dados

| Ação   | Descrição                                       | Migration Necessária? |
|--------|------------------------------------------------|-----------------------|
| Criar  | Tabela `score_historico` para persistir score mensal | Sim                |

**Migration:**

```sql
CREATE TABLE score_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes_referencia DATE NOT NULL UNIQUE,
    score_total INTEGER NOT NULL CHECK (score_total >= 0 AND score_total <= 100),
    d1_comprometimento INTEGER NOT NULL CHECK (d1_comprometimento >= 0 AND d1_comprometimento <= 25),
    d2_parcelas INTEGER NOT NULL CHECK (d2_parcelas >= 0 AND d2_parcelas <= 25),
    d3_poupanca INTEGER NOT NULL CHECK (d3_poupanca >= 0 AND d3_poupanca <= 25),
    d4_comportamento INTEGER NOT NULL CHECK (d4_comportamento >= 0 AND d4_comportamento <= 25),
    classificacao VARCHAR(20) NOT NULL,
    score_conservador INTEGER,
    dados_snapshot JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_score_mes ON score_historico(mes_referencia);
```

---

## 11. Tarefas de Implementação

| ID      | Tarefa                                                          | Depende de | Done When                                                        |
|---------|-----------------------------------------------------------------|------------|------------------------------------------------------------------|
| CR4-T01 | Criar migration da tabela `score_historico`                     | —          | Tabela criada, migration reversível funcionando                  |
| CR4-T02 | Criar modelo ORM `ScoreHistorico`                               | CR4-T01    | Modelo mapeado com validações e CRUD funcional                   |
| CR4-T03 | Criar serviço `health_score.py` com cálculo das 4 dimensões    | —          | Função `calcular_score(dados)` retorna score total + breakdown. Testes passam para todos os cenários da seção 14 |
| CR4-T04 | Criar serviço `health_score_actions.py`                         | CR4-T03    | Função `gerar_acoes(score_breakdown, dados)` retorna top 3 ações com impacto estimado |
| CR4-T05 | Criar schemas Pydantic para score                               | CR4-T03    | Request/response tipados para endpoints                          |
| CR4-T06 | Criar endpoint GET `/api/score`                                 | CR4-T03, CR4-T04, CR4-T05 | Retorna score atual com breakdown, classificação, ações, cenário conservador e variação vs. mês anterior |
| CR4-T07 | Criar endpoint GET `/api/score/history?months=12`               | CR4-T02, CR4-T05 | Retorna array de scores mensais para gráfico de evolução    |
| CR4-T08 | Implementar persistência automática do score mensal             | CR4-T02, CR4-T03 | Ao calcular score, salva/atualiza registro do mês corrente no `score_historico` com snapshot |
| CR4-T09 | Testes unitários do serviço de cálculo                          | CR4-T03    | 100% dos cenários da seção 14 cobertos e passando                |
| CR4-T10 | Testes unitários do gerador de ações                            | CR4-T04    | Ações geradas corretamente para cada combinação de dimensão baixa |
| CR4-T11 | Criar types TypeScript para score                               | CR4-T05    | Types refletem schemas do backend                                |
| CR4-T12 | Criar hook `useHealthScore`                                     | CR4-T11    | Hook consome endpoints e retorna score + history + loading + error |
| CR4-T13 | Criar componente `ScoreGauge`                                   | CR4-T12    | Gauge circular animado com nota, cor semafórica, classificação. Versão compacta (dashboard) e expandida (detalhe) |
| CR4-T14 | Criar componente `ScoreDimensionBreakdown`                      | CR4-T12    | 4 barras horizontais com label, pontuação (X/25), cor proporcional, tooltip com explicação |
| CR4-T15 | Criar componente `ScoreHistoryChart`                            | CR4-T12    | Gráfico de linha com pontos por mês, tooltip com nota e classificação, faixas de cor de fundo (vermelho→verde) |
| CR4-T16 | Criar componente `ScoreActions`                                 | CR4-T12    | Cards com ícone, descrição da ação, impacto estimado ("↑ ~X pontos"), ordenados por impacto |
| CR4-T17 | Criar componente `ScoreConservativeNote`                        | CR4-T12    | Banner de alerta visível quando existem parcelas pendentes, mostrando score conservador |
| CR4-T18 | Criar tela `ScoreDetail`                                        | CR4-T13, CR4-T14, CR4-T15, CR4-T16, CR4-T17 | Tela completa: gauge grande + breakdown + histórico + ações + cenário conservador |
| CR4-T19 | Adicionar card de score no Dashboard (F02)                      | CR4-T13    | ScoreGauge compacto no dashboard com variação mensal e link para ScoreDetail |
| CR4-T20 | Configurar navegação Dashboard → ScoreDetail                    | CR4-T18, CR4-T19 | Toque no card navega para tela de detalhe com transição suave |
| CR4-T21 | Testes de integração frontend                                   | CR4-T20    | Componentes renderizam com dados mock, cenários de borda, responsivo |
| CR4-T22 | Atualizar documentação (SPEC.md, PRD.md)                        | CR4-T20    | Documentos refletem score implementado, modelo de cálculo documentado |

---

## 12. Critérios de Aceite

| #  | Critério                                                                                  | Tipo       |
|----|-------------------------------------------------------------------------------------------|------------|
| 1  | DADO que o usuário tem despesas e receitas cadastradas QUANDO acessa o Dashboard ENTÃO o card de score exibe gauge circular com nota (0-100), cor semafórica e classificação textual | Funcional |
| 2  | DADO que o usuário tem histórico do mês anterior QUANDO o card de score é renderizado ENTÃO exibe variação vs. mês anterior (ex: "↑ +5" ou "↓ -3") | Funcional |
| 3  | DADO que o usuário toca no card de score QUANDO a navegação ocorre ENTÃO a tela de detalhe é exibida com gauge grande, breakdown das 4 dimensões, histórico, ações e cenário conservador | Funcional |
| 4  | DADO comprometimento fixo de 64% da renda QUANDO D1 é calculada ENTÃO o resultado é 12 pontos (faixa 60,1%-70%) | Cálculo |
| 5  | DADO 11 parcelas ativas com 2 pendentes e 4 encerrando em 3 meses liberando > 10% QUANDO D2 é calculada ENTÃO subfatores D2a + D2b + D2c + D2d são calculados e total é clamped entre 0 e 25 | Cálculo |
| 6  | DADO saldo livre real de 15% da renda QUANDO D3 é calculada ENTÃO o resultado é 20 pontos (faixa 15%-19,9%) | Cálculo |
| 7  | DADO 100% das despesas pagas em dia e 15 dias de registro QUANDO D4 é calculada ENTÃO D4a = 10, D4b = min(5, (15/20)*5) = 3 | Cálculo |
| 8  | DADO que é o primeiro mês de uso (sem histórico) QUANDO D4c é calculada ENTÃO assume 3 pontos (neutro) | Edge case |
| 9  | DADO que o score foi calculado QUANDO o mês é o corrente ENTÃO o registro em `score_historico` é criado/atualizado com snapshot dos dados | Persistência |
| 10 | DADO que existem 6 meses de histórico QUANDO a tela de detalhe é exibida ENTÃO o gráfico de evolução mostra 6 pontos conectados por linha | Funcional |
| 11 | DADO que a dimensão D2 tem menor pontuação E existem parcelas encerrando em breve QUANDO as ações são geradas ENTÃO a ação "redirecionar valor da parcela X que termina em Y" aparece com impacto estimado | Funcional |
| 12 | DADO que existem parcelas pendentes (0 de Y) QUANDO a tela de detalhe é renderizada ENTÃO o banner de cenário conservador é exibido com score recalculado incluindo parcelas pendentes como ativas | Funcional |
| 13 | DADO que o score atual é 50 e a ação sugere reduzir categoria Alimentação QUANDO o impacto é calculado ENTÃO o sistema recalcula o score com o cenário hipotético e mostra "↑ ~X pontos" | Funcional |
| 14 | DADO que não existem receitas cadastradas QUANDO o score é calculado ENTÃO retorna score 0 com mensagem "Cadastre sua renda para calcular o score" | Edge case |
| 15 | DADO que não existem despesas cadastradas QUANDO o score é calculado ENTÃO retorna score 100 com as 4 dimensões no máximo | Edge case |
| 16 | O endpoint GET `/api/score` responde em menos de 200ms                                    | Performance |
| 17 | A tela de detalhe e o card do dashboard são responsivos de 320px a 1920px                 | UI |
| 18 | O score calculado para os mesmos dados de entrada SEMPRE retorna o mesmo resultado (determinístico) | Não-funcional |

---

## 13. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                                        | Probabilidade | Mitigação                                                       |
|----|-----------------------------------------------------------------|---------------|-----------------------------------------------------------------|
| 1  | Estimativa de gastos variáveis imprecisa no primeiro mês        | Alta          | Usar projeção proporcional (total_variáveis * 30/dias_registrados). Exibir indicador "estimativa baseada em X dias de dados" quando < 15 dias |
| 2  | Score diverge do score futuro da IA (F06)                       | Média         | Opção B definida: IA recebe score local como input e contextualiza, nunca recalcula. Ajustar prompt da F06 quando implementar |
| 3  | Faixas de classificação podem não refletir a realidade brasileira | Média       | Calibrar faixas com dados reais após 2-3 meses de uso. Manter faixas configuráveis (não hardcoded) |
| 4  | Usuário pode ficar desmotivado com score muito baixo             | Média         | Mensagens empáticas (nunca punitivas). Sempre mostrar ações concretas para melhorar. Frase contextual foca no progresso possível, não na falha |
| 5  | Recálculo frequente do score ao longo do mês pode confundir      | Baixa         | O score do mês é o "último cálculo". O snapshot final é salvo na virada do mês. Durante o mês, é um score "em progresso" |

---

## 14. Cenários de Teste do Cálculo

### Cenário 1: Situação saudável
- Renda: R$ 10.000
- Fixos: R$ 4.500 (45%)
- Parcelas: 2 ativas (R$ 800 total, 8%), nenhuma pendente
- Variáveis: R$ 2.000 (20%)
- Saldo livre: 35%
- Tudo pago em dia, 22 dias de registro, comprometimento reduziu vs. mês anterior
- **Esperado:** D1=25, D2≈18, D3=25, D4≈23 → **Score ~91 (Excelente)**

### Cenário 2: Dados reais Fev/2026 (Rafael)
- Renda: R$ 17.619,55
- Fixos: R$ 11.296,76 (64,1%)
- Parcelas: 11 ativas (~41,6% da renda em parcelas), 2 pendentes, 4 encerrando em 3 meses liberando ~7%
- Variáveis estimados: ~R$ 3.800 (projeção 4 dias)
- Saldo livre real: ~14,3% (com variáveis projetados)
- Tudo pago em dia, 4 dias de registro
- **Esperado:** D1=12, D2≈3, D3=15, D4≈15 → **Score ~45 (Atenção)**
- **Score conservador (com Itaú e Sonia ativados):** ~30 (Atenção)

### Cenário 3: Primeiro mês, poucos dados
- Renda: R$ 8.000
- Fixos: R$ 3.000 (37,5%)
- Parcelas: nenhuma
- Variáveis: R$ 500 em 5 dias (projeção ~R$ 3.000)
- Saldo livre: ~25%
- 5 dias de registro, sem histórico anterior
- **Esperado:** D1=25, D2=25, D3=25, D4≈14 → **Score ~89 (Excelente)**

### Cenário 4: Situação crítica
- Renda: R$ 5.000
- Fixos: R$ 4.500 (90%)
- Parcelas: 12 ativas (60% da renda), 3 pendentes
- Variáveis: R$ 1.500
- Saldo livre: negativo (-R$ 1.000)
- 3 despesas atrasadas, 2 dias de registro, comprometimento aumentou
- **Esperado:** D1=0, D2=0, D3=0, D4≈3 → **Score ~3 (Crítica)**

### Cenário 5: Sem receitas cadastradas
- Renda: R$ 0 (não cadastrou)
- **Esperado:** Score 0, mensagem "Cadastre sua renda para calcular o score"

### Cenário 6: Sem despesas cadastradas
- Renda: R$ 10.000
- Fixos: R$ 0
- **Esperado:** D1=25, D2=25, D3=25, D4=25 → **Score 100 (Excelente)**

---

## 15. Estrutura de resposta dos endpoints

### GET /api/score

```json
{
  "score": {
    "total": 45,
    "classificacao": "atenção",
    "cor": "#E67E22",
    "mensagem": "Alguns pontos precisam de ajuste",
    "mensagem_contextual": "Sua principal oportunidade: reduzir a pressão de parcelas. O Empr. Sonia termina em 2 meses, o que pode melhorar seu score.",
    "variacao_mes_anterior": null,
    "mes_referencia": "2026-02"
  },
  "dimensoes": {
    "d1_comprometimento": {
      "pontos": 12,
      "maximo": 25,
      "percentual_comprometimento": 64.1,
      "detalhe": "Gastos fixos consomem 64,1% da renda (ideal: até 50%)"
    },
    "d2_parcelas": {
      "pontos": 3,
      "maximo": 25,
      "subfatores": {
        "d2a_percentual": { "pontos": 4, "valor": 35.2 },
        "d2b_quantidade": { "pontos": 0, "valor": 11 },
        "d2c_pendentes": { "pontos": -5, "quantidade": 2 },
        "d2d_alivio": { "pontos": 3, "percentual_liberacao": 7.0 }
      },
      "detalhe": "11 parcelas ativas com 2 pendentes. Pressão alta."
    },
    "d3_poupanca": {
      "pontos": 15,
      "maximo": 25,
      "percentual_livre": 14.3,
      "estimativa_variáveis": true,
      "dias_dados_variaveis": 4,
      "detalhe": "Saldo livre estimado em 14,3% (baseado em 4 dias de dados)"
    },
    "d4_comportamento": {
      "pontos": 15,
      "maximo": 25,
      "subfatores": {
        "d4a_pontualidade": { "pontos": 10, "percentual_em_dia": 100 },
        "d4b_consistencia": { "pontos": 1, "dias_registro": 4 },
        "d4c_tendencia": { "pontos": 3, "primeiro_mes": true },
        "d4d_disciplina": { "pontos": 0, "nova_parcela_longa": "Empr. PicPay 48x" }
      },
      "detalhe": "Pagamentos em dia, mas poucos dias de registro"
    }
  },
  "cenario_conservador": {
    "score": 30,
    "classificacao": "atenção",
    "parcelas_pendentes": [
      { "descricao": "Empr. Itaú", "valor_estimado_mensal": 2726.52, "total_parcelas": 60 },
      { "descricao": "Empr. Sonia 11x", "valor_estimado_mensal": 500.00, "total_parcelas": 11 }
    ],
    "impacto": "Se ativadas, comprometimento sobe para ~79,6%"
  },
  "acoes": [
    {
      "prioridade": 1,
      "dimensao_alvo": "d2_parcelas",
      "descricao": "O Empr. Sonia termina em 2 meses. Redirecionar R$ 500/mês para poupança.",
      "impacto_estimado": 4,
      "tipo": "oportunidade"
    },
    {
      "prioridade": 2,
      "dimensao_alvo": "d1_comprometimento",
      "descricao": "Revisar assinaturas de streaming (R$ 184,70/mês). Cancelar 1-2 pode reduzir comprometimento.",
      "impacto_estimado": 2,
      "tipo": "redução"
    },
    {
      "prioridade": 3,
      "dimensao_alvo": "d4_comportamento",
      "descricao": "Registrar gastos diários com mais frequência. Meta: 15+ dias no mês.",
      "impacto_estimado": 3,
      "tipo": "habito"
    }
  ]
}
```

### GET /api/score/history?months=12

```json
{
  "historico": [
    {
      "mes_referencia": "2026-02",
      "score_total": 45,
      "classificacao": "atenção",
      "d1": 12,
      "d2": 3,
      "d3": 15,
      "d4": 15
    }
  ],
  "meses_solicitados": 12,
  "meses_disponiveis": 1
}
```

---

## 16. Integração futura com F06 (Análise IA)

Quando F06 for implementada, o prompt de análise financeira será ajustado para receber o score como input (Opção B):

```
<score_saude_financeira>
  Score atual: {{score_total}}/100 ({{classificacao}})
  D1 - Comprometimento: {{d1}}/25
  D2 - Parcelas: {{d2}}/25
  D3 - Poupança: {{d3}}/25
  D4 - Comportamento: {{d4}}/25
  Cenário conservador: {{score_conservador}}/100
</score_saude_financeira>

Considere este score como a métrica oficial. NÃO recalcule o score.
Use-o como base para contextualizar suas recomendações e análise qualitativa.
```

O campo `score_saude_financeira` será REMOVIDO do output JSON da IA. A IA se concentrará em: diagnóstico qualitativo, alertas, recomendações detalhadas, metas e mensagem motivacional.

---

## 17. Changelog

| Versão | Data       | Autor           | Descrição           |
|--------|------------|-----------------|---------------------|
| 1.0    | 2026-03-16 | Rafael Peixoto  | Criação do CR-004   |
| 1.1    | 2026-03-16 | Claude          | Implementação concluída |
