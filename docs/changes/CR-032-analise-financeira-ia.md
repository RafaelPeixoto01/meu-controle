# Change Request — CR-006: Análise Financeira por IA

**Versão:** 1.0  
**Data:** 2026-03-17  
**Status:** Concluído  
**Autor:** Rafael Peixoto  
**Prioridade:** Crítica

---

## 1. Resumo da Mudança

Integrar o prompt de análise financeira por IA (já desenhado e simulado com dados reais) na aba "Score" do MeuControle. A tela de Score será reorganizada em scroll único intercalando os componentes existentes do score (F04) com as novas seções de análise da IA. A análise é gerada automaticamente na virada do mês (modo mensal), usando a API Claude para produzir diagnóstico qualitativo, alertas, recomendações, metas e mensagem motivacional. A IA recebe o score determinístico da F04 como input e o contextualiza sem recalcular (Opção B). O prompt existente será refatorado para: remover cálculo de score, incluir dados de categorias (F01), projeção de parcelas (F03) e histórico de scores (F04), e endurecer o contrato de output JSON para renderização na UI. A análise sob demanda (botão na seção de análise) será implementada em fase futura.

---

## 2. Classificação

| Campo            | Valor                                                                 |
|------------------|-----------------------------------------------------------------------|
| Tipo             | Nova Feature (evolução de tela existente + integração com API externa) |
| Origem           | Roadmap F06 (Benchmark competitivo + prompt já desenhado)             |
| Urgência         | Próxima sprint                                                        |
| Complexidade     | Alta                                                                  |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

A aba "Score" exibe (conforme tela implementada):
1. Gauge circular com nota (0-100), classificação, mensagem contextual e variação vs. mês anterior
2. Detalhamento por dimensão (D1-D4) com barras horizontais, pontuação X/25 e descrição curta
3. Seção "Como melhorar" com até 3 ações sugeridas (calculadas localmente pela F04)
4. Gráfico "Evolução do score" com linha temporal e tooltips por mês

O prompt de análise financeira por IA existe como documento isolado (`prompt-analise-financeira.md`) com:
- Estrutura de dados de entrada definida
- Instruções de análise em 6 etapas
- Output JSON estruturado com: diagnóstico, alertas, bons comportamentos, recomendações, metas e mensagem motivacional
- Simulação já validada com dados reais de fevereiro/2026 (score 38, alertas sobre Itaú 60x, detecção de streamings)

O prompt NÃO está integrado ao app. A IA não é chamada. Os dados não são coletados automaticamente.

### Problema ou Necessidade

1. **Análise qualitativa ausente**: a F04 calcula o score e sugere ações genéricas baseadas em fórmulas. Falta a camada de interpretação humana que a IA oferece: "seus gastos com delivery cresceram 15% e representam mais que o benchmark", "considere negociar o empréstimo PicPay que tem as piores condições".
2. **Prompt existe mas está desconectado**: o investimento de design do prompt (estrutura, tom, formato JSON) não gera valor enquanto não estiver integrado.
3. **Detecção de padrões impossível sem IA**: identificar "gastos recorrentes disfarçados de variáveis" (iFood 18x/mês), picos de gasto por dia da semana, e oportunidades de renegociação requer interpretação que fórmulas não fazem.
4. **Engajamento mensal**: a análise automática na virada do mês cria um ritual de revisão financeira (similar ao "Month in Review" do Monarch) que é um dos mecanismos de retenção mais fortes identificados no benchmark.

### Situação Desejada (TO-BE)

A aba "Score" será reorganizada em scroll único com a seguinte estrutura intercalada:

```
┌─────────────────────────────────────────┐
│ GAUGE DO SCORE (existente F04)          │
│ 50/100 - Estável - variação mensal      │
├─────────────────────────────────────────┤
│ DIAGNÓSTICO IA (novo)                   │
│ Resumo geral + categorias em destaque   │
├─────────────────────────────────────────┤
│ DETALHAMENTO POR DIMENSÃO (existente)   │
│ D1, D2, D3, D4 com barras              │
├─────────────────────────────────────────┤
│ ALERTAS IA (novo)                       │
│ Críticos → Atenção → Informativos       │
├─────────────────────────────────────────┤
│ COMO MELHORAR (existente, enriquecido)  │
│ Ações da F04 + Recomendações da IA      │
├─────────────────────────────────────────┤
│ BONS COMPORTAMENTOS (novo)              │
│ Reforço positivo da IA                  │
├─────────────────────────────────────────┤
│ METAS SUGERIDAS (novo)                  │
│ Curto / Médio / Longo prazo             │
├─────────────────────────────────────────┤
│ GASTOS RECORRENTES DISFARÇADOS (novo)   │
│ Variáveis que deveriam ser fixos        │
├─────────────────────────────────────────┤
│ MENSAGEM MOTIVACIONAL (novo)            │
│ Frase personalizada da IA               │
├─────────────────────────────────────────┤
│ EVOLUÇÃO DO SCORE (existente)           │
│ Gráfico de linha temporal               │
├─────────────────────────────────────────┤
│ FOOTER                                  │
│ Disclaimer IA + data da análise         │
└─────────────────────────────────────────┘
```

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                              | Antes (AS-IS)                                        | Depois (TO-BE)                                                                      |
|----|-----------------------------------|------------------------------------------------------|-------------------------------------------------------------------------------------|
| 1  | Layout da aba Score               | 4 seções sequenciais (gauge, dimensões, ações, evolução) | Scroll único com seções do score intercaladas com seções da análise IA (10 seções)  |
| 2  | Fonte dos dados de análise        | Nenhuma (prompt isolado)                             | Backend coleta dados de F01/F03/F04, monta prompt, chama API Claude, parseia JSON   |
| 3  | Seção "Como melhorar"             | Apenas ações calculadas localmente (F04)             | Ações da F04 + recomendações da IA mescladas, ordenadas por impacto estimado        |
| 4  | Diagnóstico qualitativo           | Inexistente                                          | Resumo geral da IA com comparativo benchmark e categorias em destaque               |
| 5  | Alertas financeiros               | Inexistentes                                         | Lista priorizada (crítico/atenção/informativo) com impacto em R$                    |
| 6  | Bons comportamentos               | Inexistentes                                         | Reforço positivo de hábitos saudáveis detectados pela IA                            |
| 7  | Metas sugeridas                   | Inexistentes                                         | 3 metas (curto/médio/longo prazo) com valor-alvo e primeiro passo                   |
| 8  | Gastos recorrentes disfarçados    | Inexistentes                                         | Detecção de variáveis que aparecem todo mês (delivery, café, etc.)                  |
| 9  | Mensagem motivacional             | Inexistente                                          | Frase personalizada conectada aos dados reais                                       |
| 10 | Geração da análise                | Manual (rodar prompt fora do app)                    | Automática na virada do mês (primeiro acesso do mês seguinte)                       |
| 11 | Prompt de análise                 | Versão original com cálculo de score                 | Versão refatorada: sem score, com categorias, projeção parcelas, histórico scores   |
| 12 | Persistência                      | Nenhuma                                              | Tabela `analise_financeira` com resultado JSON, dados de input, metadata de API     |

### 4.2 O que NÃO muda

- Cálculo do score (F04) permanece determinístico e local — a IA não recalcula
- Componentes existentes da aba Score (gauge, dimensões, evolução) mantêm comportamento atual
- Prompt não é alterado em tom/diretrizes — apenas reestruturado para integração
- Demais abas (Dashboard, Gastos Planejados, Gastos Diários, Parcelas) não são afetadas
- Análise sob demanda NÃO é implementada nesta CR (fase futura)

---

## 5. Prompt refatorado

### 5.1 System prompt

```
Você é um consultor financeiro pessoal especializado em análise comportamental 
de gastos. Sua função é analisar os dados financeiros do usuário e fornecer 
orientações práticas, empáticas e personalizadas.

REGRAS:
1. O score de saúde financeira já foi calculado pelo sistema (veja 
   <score_saude_financeira>). NÃO recalcule este score. Use-o como referência 
   para contextualizar suas recomendações.
2. Responda APENAS com o JSON especificado. Sem texto adicional, sem markdown, 
   sem backticks.
3. Respeite os limites de caracteres de cada campo.
4. Seja direto mas empático. Nunca julgue ou use tom punitivo.
5. Use linguagem acessível em português brasileiro.
6. Contextualize para a realidade brasileira (custo de vida, cultura de 
   parcelamento, Pix, etc.).
7. Priorize ações práticas sobre conselhos genéricos.
8. Quando identificar um problema sério, comunique com cuidado mas sem minimizar.
9. A mensagem motivacional deve ser genuína e conectada aos dados reais.
10. Nos campos de impacto_score_estimado das recomendações, estime quantos pontos 
    o score subiria se a ação fosse implementada, baseado nas dimensões afetadas.
```

### 5.2 User prompt (template com placeholders)

```
Analise os dados financeiros abaixo e retorne sua análise no formato JSON especificado.

<dados_financeiros>

<score_saude_financeira>
  Score atual: {{score_total}}/100 ({{classificacao}})
  D1 - Comprometimento com fixos: {{d1}}/25 — {{d1_detalhe}}
  D2 - Pressão de parcelas: {{d2}}/25 — {{d2_detalhe}}
  D3 - Capacidade de poupança: {{d3}}/25 — {{d3_detalhe}}
  D4 - Comportamento e disciplina: {{d4}}/25 — {{d4_detalhe}}
  Cenário conservador (com parcelas pendentes): {{score_conservador}}/100
  Histórico: {{historico_scores}}
</score_saude_financeira>

<resumo_mensal>
  Mês de referência: {{mes_referencia}}
  Renda líquida mensal: R$ {{renda_liquida}}
  Total de gastos planejados (fixos): R$ {{total_planejados}}
  Total de gastos não planejados (variáveis): R$ {{total_nao_planejados}}
  Total comprometido com parcelas: R$ {{total_parcelas}}
  Saldo restante: R$ {{saldo_restante}}
  Dias de registro de gastos diários: {{dias_registro}}
</resumo_mensal>

<gastos_por_categoria>
  {{breakdown_categorias}}
</gastos_por_categoria>

<gastos_planejados>
  {{lista_gastos_planejados}}
</gastos_planejados>

<gastos_nao_planejados_ultimos_3_meses>
  {{lista_gastos_nao_planejados}}
</gastos_nao_planejados_ultimos_3_meses>

<parcelas_ativas>
  {{lista_parcelas}}
</parcelas_ativas>

<projecao_parcelas_proximos_3_meses>
  {{projecao_3_meses}}
</projecao_parcelas_proximos_3_meses>

<historico_mensal>
  {{comparativo_ultimos_meses}}
</historico_mensal>

</dados_financeiros>

Retorne APENAS o JSON abaixo preenchido. Sem texto antes ou depois.

{
  "diagnostico": {
    "resumo_geral": "string (2-3 frases, max 300 chars)",
    "comparativo_benchmark": "string (max 200 chars)",
    "variacao_vs_mes_anterior": "string | null (max 150 chars)",
    "categorias_destaque": [
      {
        "categoria": "string",
        "percentual_renda": 0.0,
        "benchmark_saudavel": 0.0,
        "variacao_mensal_percentual": 0.0,
        "observacao": "string (max 120 chars)"
      }
    ]
  },
  "alertas": [
    {
      "tipo": "critico | atencao | informativo",
      "titulo": "string (max 60 chars)",
      "descricao": "string (max 200 chars)",
      "impacto_mensal": 0.0,
      "impacto_anual": 0.0
    }
  ],
  "bons_comportamentos": [
    {
      "comportamento": "string (max 80 chars)",
      "mensagem_reforco": "string (max 150 chars)"
    }
  ],
  "recomendacoes": [
    {
      "prioridade": 1,
      "acao": "string (max 100 chars)",
      "justificativa": "string (max 200 chars)",
      "economia_estimada_mensal": 0.0,
      "dificuldade": "fácil | moderada | difícil",
      "impacto_score_estimado": 0
    }
  ],
  "metas": {
    "curto_prazo": {
      "descricao": "string (max 120 chars)",
      "valor_alvo": 0.0,
      "prazo_meses": 0,
      "primeiro_passo": "string (max 100 chars)"
    },
    "medio_prazo": {
      "descricao": "string (max 120 chars)",
      "valor_alvo": 0.0,
      "prazo_meses": 0,
      "primeiro_passo": "string (max 100 chars)"
    },
    "longo_prazo": {
      "descricao": "string (max 120 chars)",
      "valor_alvo": 0.0,
      "prazo_meses": 0,
      "primeiro_passo": "string (max 100 chars)"
    }
  },
  "gastos_recorrentes_disfarcados": [
    {
      "descricao": "string (max 80 chars)",
      "frequencia_mensal": 0,
      "valor_medio_mensal": 0.0,
      "sugestao": "string (max 120 chars)"
    }
  ],
  "mensagem_motivacional": "string (max 300 chars)"
}
```

### 5.3 Limites de campos no output

| Campo | Quantidade máxima | Justificativa |
|-------|------------------|---------------|
| `categorias_destaque` | 5 | Top 5 categorias mais relevantes para não sobrecarregar a UI |
| `alertas` | 5 | Máximo 5 alertas, ordenados por severidade |
| `bons_comportamentos` | 3 | Máximo 3 para manter impacto |
| `recomendacoes` | 5 | Máximo 5, ordenadas por prioridade |
| `gastos_recorrentes_disfarcados` | 5 | Máximo 5, se existirem |
| `metas` | 3 (fixo) | Sempre 3: curto, médio, longo prazo |

---

## 6. Pipeline de execução

### 6.1 Fluxo da análise mensal automática

```
Usuário acessa aba "Score" no primeiro acesso do mês
         │
         ▼
Backend verifica: existe análise persistida para o mês ANTERIOR?
         │
    ┌────┴────┐
    │ SIM     │ NÃO
    │         │
    ▼         ▼
Exibe       Verifica: mês anterior tem dados suficientes?
análise     (≥ 7 dias de registro OU ≥ 5 despesas planejadas)
salva            │
              ┌──┴──┐
              │SIM  │NÃO
              │     │
              ▼     ▼
         Gera análise   Exibe seção de análise com
         automaticamente estado: "Dados insuficientes
              │         para análise do mês anterior"
              ▼
         1. Coletor agrega dados do mês anterior
         2. Montador injeta no template de prompt
         3. Chamada API Claude (Sonnet)
         4. Parsing do JSON com validação
         5. Persistência na tabela analise_financeira
         6. Renderização na UI
```

### 6.2 Lógica de disparo

A análise é gerada para o **mês anterior** (mês fechado), não para o mês corrente. Motivo: garantir que os dados estão completos.

- **Quando:** primeiro acesso à aba Score a partir do dia 1 do mês seguinte
- **Mês de referência:** mês anterior (ex: acessa em 01/abril → analisa março)
- **Dados mínimos:** ≥ 7 dias de gastos diários registrados OU ≥ 5 despesas planejadas
- **Se dados insuficientes:** exibe mensagem na seção de análise, sem chamar API
- **Se análise já existe para o mês:** exibe resultado persistido, sem nova chamada

### 6.3 Estado de loading

Enquanto a análise é gerada (5-15 segundos):
- Seções do score (gauge, dimensões, evolução) renderizam normalmente (dados locais, instantâneos)
- Seções da análise IA exibem skeleton loading com mensagem: "Gerando sua análise financeira..."
- Após conclusão: seções da IA aparecem com animação suave (fade-in)

---

## 7. Reorganização da tela de Score

### 7.1 Layout atual (AS-IS)

```
1. Gauge do score (nota, classificação, variação)
2. Detalhamento por dimensão (D1-D4)
3. Como melhorar (3 ações da F04)
4. Evolução do score (gráfico de linha)
```

### 7.2 Layout novo (TO-BE) — scroll único intercalado

```
1. GAUGE DO SCORE (existente, sem alteração)
   - Nota 50/100, "Estável", variação -15 pontos
   
2. DIAGNÓSTICO IA (novo)
   - Card com resumo geral (2-3 frases)
   - Comparativo benchmark ("regra 50/30/20")
   - Variação vs. mês anterior (se disponível)
   - Pills de categorias em destaque com % e variação (verde/vermelho)
   - Se análise não disponível: placeholder "Análise disponível após o fechamento do mês"

3. DETALHAMENTO POR DIMENSÃO (existente, sem alteração)
   - D1: Comprometimento com fixos — 12/25
   - D2: Pressão de parcelas — 17/25
   - D3: Capacidade de poupança — 0/25
   - D4: Comportamento e disciplina — 21/25

4. ALERTAS (novo)
   - Cards ordenados por severidade
   - Ícone + cor: 🔴 crítico, 🟡 atenção, 🔵 informativo
   - Título em negrito + descrição + impacto em R$/mês e R$/ano
   - Se nenhum alerta: não exibe a seção

5. COMO MELHORAR (existente, enriquecido)
   - Mescla ações da F04 (calculadas localmente) com recomendações da IA
   - Ordenadas por impacto estimado no score (maior primeiro)
   - Badge de dificuldade (fácil/moderada/difícil)
   - Impacto: "↑ ~5 pontos" + economia estimada "R$ 250/mês"
   - Sem duplicação: se F04 e IA sugerem algo similar, prevalece a versão da IA (mais contextualizada)

6. BONS COMPORTAMENTOS (novo)
   - Cards com ícone ✅ verde
   - Comportamento identificado + mensagem de reforço
   - Se nenhum: não exibe a seção

7. METAS SUGERIDAS (novo)
   - 3 cards horizontais com scroll ou empilhados
   - Cada card: ícone de horizonte (🎯 curto, 📈 médio, 🏆 longo)
   - Descrição + valor-alvo + prazo + primeiro passo destacado
   - Se análise não disponível: não exibe a seção

8. GASTOS RECORRENTES DISFARÇADOS (novo)
   - Header: "Variáveis que parecem fixos"
   - Lista: descrição, frequência, valor médio, sugestão
   - Ex: "iFood — 18x/mês — R$ 890/mês — Considere incluir como gasto planejado"
   - Se nenhum detectado: não exibe a seção

9. MENSAGEM MOTIVACIONAL (novo)
   - Card com fundo sutil (gradiente leve ou cor de destaque)
   - Frase personalizada da IA, conectada aos dados reais
   - Se análise não disponível: não exibe

10. EVOLUÇÃO DO SCORE (existente, sem alteração)
    - Gráfico de linha com pontos mensais
    - Tooltip com score e breakdown por dimensão

11. FOOTER (novo)
    - Texto pequeno: "Análise gerada por IA em [data]. Valores e recomendações são estimativas baseadas nos seus dados."
    - Mês de referência da análise
```

### 7.3 Regra de exibição das seções de IA

| Condição | Seções IA exibidas | Comportamento |
|----------|-------------------|---------------|
| Análise disponível (persistida) | Todas as 6 seções novas | Renderiza normalmente com dados do JSON |
| Análise sendo gerada (loading) | Todas as 6 seções com skeleton | Seções do score renderizam instantaneamente, seções IA em loading |
| Análise não disponível (primeiro mês ou dados insuficientes) | Apenas placeholder no lugar do Diagnóstico | Mensagem: "Sua primeira análise será gerada após o fechamento do mês, quando houver dados suficientes." |
| Erro na geração da análise | Placeholder com retry | Mensagem: "Não foi possível gerar a análise. Tente novamente mais tarde." + botão "Tentar novamente" |

---

## 8. Mesclagem da seção "Como melhorar"

A seção "Como melhorar" existente (F04) e as "Recomendações" da IA precisam ser mescladas em uma única seção para evitar duplicação e confusão.

### Regras de mesclagem

1. **Fonte primária:** recomendações da IA (mais contextualizadas e com justificativa qualitativa)
2. **Complemento:** ações da F04 que não foram cobertas pela IA
3. **Deduplicação:** se a F04 sugere "Revisar despesas fixas não essenciais" e a IA sugere "Considerar cancelar Disney+ ou Netflix para reduzir comprometimento", a versão da IA prevalece por ser mais específica
4. **Ordenação final:** por `impacto_score_estimado` decrescente (maior impacto primeiro)
5. **Máximo exibido:** 5 ações (evitar lista longa)
6. **Fallback:** se análise IA não disponível, exibe apenas ações da F04 (comportamento atual)

### Lógica de deduplicação (pseudocódigo)

```python
def mesclar_acoes(acoes_f04: list, recomendacoes_ia: list) -> list:
    resultado = []
    
    # Primeiro, todas as recomendações da IA
    for rec_ia in recomendacoes_ia:
        resultado.append({
            "fonte": "ia",
            "acao": rec_ia["acao"],
            "justificativa": rec_ia["justificativa"],
            "impacto_score": rec_ia["impacto_score_estimado"],
            "economia_mensal": rec_ia["economia_estimada_mensal"],
            "dificuldade": rec_ia["dificuldade"],
        })
    
    # Depois, ações da F04 que não têm equivalente na IA
    # Equivalência: mesma dimensão-alvo
    dimensoes_cobertas_ia = {r["dimensao_alvo"] for r in recomendacoes_ia if "dimensao_alvo" in r}
    
    for acao_f04 in acoes_f04:
        if acao_f04["dimensao_alvo"] not in dimensoes_cobertas_ia:
            resultado.append({
                "fonte": "score",
                "acao": acao_f04["descricao"],
                "justificativa": None,
                "impacto_score": acao_f04["impacto_estimado"],
                "economia_mensal": None,
                "dificuldade": None,
            })
    
    # Ordenar por impacto e limitar
    resultado.sort(key=lambda x: x["impacto_score"], reverse=True)
    return resultado[:5]
```

---

## 9. Impacto nos Documentos

| Documento                          | Impactado? | Seções Afetadas                        | Ação Necessária                                   |
|------------------------------------|------------|----------------------------------------|---------------------------------------------------|
| `/docs/PRD.md`                     | Sim        | Requisitos Funcionais, Roadmap         | Adicionar RF para análise IA                       |
| `/docs/ARCHITECTURE.md`            | Sim        | Modelagem de Dados, Integrações        | Adicionar tabela `analise_financeira`, documentar integração API Claude |
| `/docs/SPEC.md`                    | Sim        | Features, Endpoints, Componentes UI    | Detalhar módulo de análise IA completo             |
| `/docs/IMPLEMENTATION_PLAN.md`     | Sim        | Adicionar novo grupo de tarefas        | Inserir tarefas da F06                             |

---

## 10. Impacto no Código

### 10.1 Arquivos Afetados

| Ação      | Caminho (estimado)                                            | Descrição                                                     |
|-----------|---------------------------------------------------------------|---------------------------------------------------------------|
| Criar     | `backend/services/ai_analysis_collector.py`                   | Coletor que agrega dados de F01/F03/F04 para montar payload   |
| Criar     | `backend/services/ai_analysis_prompt.py`                      | Montador de prompt: injeta dados nos placeholders do template  |
| Criar     | `backend/services/ai_analysis_client.py`                      | Cliente da API Claude: chamada, retry, timeout, parsing JSON   |
| Criar     | `backend/services/ai_analysis_merger.py`                      | Mesclagem de ações F04 + recomendações IA                      |
| Criar     | `backend/schemas/ai_analysis.py`                              | Schemas Pydantic para input/output da análise                  |
| Criar     | `backend/routes/ai_analysis.py`                               | Endpoints: GET /api/analysis (última análise), POST /api/analysis/generate (trigger manual futuro) |
| Criar     | `backend/models/analise_financeira.py`                        | Modelo ORM para tabela `analise_financeira`                    |
| Criar     | `backend/prompts/financial_analysis_system.txt`               | System prompt (texto fixo)                                     |
| Criar     | `backend/prompts/financial_analysis_user.txt`                 | User prompt template (com placeholders)                        |
| Modificar | `backend/routes/__init__.py` (ou equivalente)                 | Registrar novas rotas                                          |
| Modificar | `backend/config.py` (ou equivalente)                          | Adicionar configuração: ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_ANALYSIS_PER_MONTH |
| Criar     | `frontend/src/components/analysis/DiagnosticoCard.tsx`        | Card de diagnóstico com resumo, benchmark, categorias           |
| Criar     | `frontend/src/components/analysis/AlertasList.tsx`            | Lista de alertas com ícones de severidade e impacto             |
| Criar     | `frontend/src/components/analysis/BonsComportamentos.tsx`     | Cards de reforço positivo                                       |
| Criar     | `frontend/src/components/analysis/MetasSugeridas.tsx`         | 3 cards de metas (curto/médio/longo)                            |
| Criar     | `frontend/src/components/analysis/GastosRecorrentes.tsx`      | Lista de variáveis disfarçados de fixos                         |
| Criar     | `frontend/src/components/analysis/MensagemMotivacional.tsx`   | Card com frase personalizada                                    |
| Criar     | `frontend/src/components/analysis/AnalysisFooter.tsx`         | Disclaimer + data da análise                                    |
| Criar     | `frontend/src/components/analysis/AnalysisPlaceholder.tsx`    | Placeholder para quando análise não está disponível             |
| Criar     | `frontend/src/hooks/useAiAnalysis.ts`                         | Hook para consumir endpoints de análise                         |
| Criar     | `frontend/src/types/aiAnalysis.ts`                            | Types TypeScript para análise                                   |
| Modificar | `frontend/src/pages/Score.tsx` (ou equivalente)               | Reorganizar layout: intercalar seções existentes com novas seções IA |
| Modificar | `frontend/src/components/score/ScoreActions.tsx` (ou equivalente) | Adaptar para receber ações mescladas (F04 + IA)            |
| Criar     | `backend/tests/test_ai_analysis_collector.py`                 | Testes do coletor de dados                                      |
| Criar     | `backend/tests/test_ai_analysis_prompt.py`                    | Testes de montagem do prompt                                    |
| Criar     | `backend/tests/test_ai_analysis_client.py`                    | Testes do cliente API (com mock)                                |
| Criar     | `backend/tests/test_ai_analysis_merger.py`                    | Testes da mesclagem de ações                                    |

### 10.2 Banco de Dados

| Ação   | Descrição                                              | Migration Necessária? |
|--------|-------------------------------------------------------|-----------------------|
| Criar  | Tabela `analise_financeira` para persistir análises    | Sim                   |

**Migration:**

```sql
CREATE TABLE analise_financeira (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mes_referencia DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'mensal',
    score_referencia INTEGER NOT NULL,
    dados_input JSONB NOT NULL,
    resultado JSONB NOT NULL,
    tokens_input INTEGER,
    tokens_output INTEGER,
    modelo VARCHAR(50) NOT NULL,
    tempo_processamento_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(mes_referencia, tipo)
);

CREATE INDEX idx_analise_mes ON analise_financeira(mes_referencia);
```

### 10.3 Configuração de ambiente

```env
# .env (adicionar)
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-20250514
AI_ANALYSIS_ENABLED=true
AI_ANALYSIS_MAX_TOKENS_INPUT=4000
AI_ANALYSIS_MAX_TOKENS_OUTPUT=2000
AI_ANALYSIS_TIMEOUT_SECONDS=30
AI_ANALYSIS_MAX_PER_MONTH=1  # MVP: apenas mensal. Futuro: 4 (1 mensal + 3 sob demanda)
```

---

## 11. Tarefas de Implementação

| ID      | Tarefa                                                          | Depende de | Done When                                                        |
|---------|-----------------------------------------------------------------|------------|------------------------------------------------------------------|
| CR6-T01 | Criar migration da tabela `analise_financeira`                  | —          | Tabela criada, migration reversível funcionando                  |
| CR6-T02 | Criar modelo ORM `AnaliseFinanceira`                            | CR6-T01    | Modelo mapeado com CRUD funcional                                |
| CR6-T03 | Criar arquivos de prompt (system + user template)               | —          | Prompts salvos em `backend/prompts/`, placeholders documentados  |
| CR6-T04 | Criar serviço `ai_analysis_collector.py`                        | —          | Função agrega dados de score (F04), categorias (F01), parcelas (F03), gastos diários, receitas e retorna dicionário completo |
| CR6-T05 | Criar serviço `ai_analysis_prompt.py`                           | CR6-T03, CR6-T04 | Função recebe dicionário de dados e retorna system prompt + user prompt com placeholders preenchidos |
| CR6-T06 | Criar serviço `ai_analysis_client.py`                           | CR6-T05    | Função chama API Claude, com: timeout 30s, retry (3x com backoff), parsing JSON, validação de campos obrigatórios, fallback para JSON malformado |
| CR6-T07 | Criar serviço `ai_analysis_merger.py`                           | —          | Função mescla ações F04 + recomendações IA: deduplicação por dimensão, ordenação por impacto, limite de 5 |
| CR6-T08 | Criar schemas Pydantic para análise                             | —          | Request/response tipados, validação de limites de caracteres e quantidades máximas |
| CR6-T09 | Criar endpoint GET `/api/analysis`                              | CR6-T02, CR6-T06, CR6-T07, CR6-T08 | Retorna última análise do mês anterior. Se não existe e dados suficientes, gera automaticamente. Se dados insuficientes, retorna 200 com status "dados_insuficientes" |
| CR6-T10 | Implementar lógica de geração automática                        | CR6-T09    | No primeiro GET do mês, se análise do mês anterior não existe, gera e persiste. Chamadas subsequentes retornam cache |
| CR6-T11 | Testes unitários do coletor                                     | CR6-T04    | Cenários: dados completos, dados parciais, primeiro mês, sem receitas |
| CR6-T12 | Testes unitários do montador de prompt                          | CR6-T05    | Prompt gerado com placeholders corretos, limites de contexto respeitados |
| CR6-T13 | Testes unitários do cliente API (com mock)                      | CR6-T06    | Cenários: resposta OK, timeout, JSON malformado, campos ausentes, retry |
| CR6-T14 | Testes unitários do merger                                      | CR6-T07    | Deduplicação correta, ordenação por impacto, limite de 5, fallback sem IA |
| CR6-T15 | Criar types TypeScript para análise                             | CR6-T08    | Types refletem schemas do backend                                |
| CR6-T16 | Criar hook `useAiAnalysis`                                      | CR6-T15    | Hook consome endpoint, retorna análise + status (loading/disponível/indisponível/erro) + retry |
| CR6-T17 | Criar componente `DiagnosticoCard`                              | CR6-T16    | Card com resumo, benchmark, pills de categorias com % e variação colorida |
| CR6-T18 | Criar componente `AlertasList`                                  | CR6-T16    | Cards por severidade com ícone colorido, impacto em R$            |
| CR6-T19 | Criar componente `BonsComportamentos`                           | CR6-T16    | Cards com ✅ verde, comportamento + reforço                       |
| CR6-T20 | Criar componente `MetasSugeridas`                               | CR6-T16    | 3 cards (curto/médio/longo) com valor-alvo, prazo, primeiro passo |
| CR6-T21 | Criar componente `GastosRecorrentes`                            | CR6-T16    | Lista de variáveis disfarçados com frequência e sugestão          |
| CR6-T22 | Criar componente `MensagemMotivacional`                         | CR6-T16    | Card com fundo sutil e frase personalizada                        |
| CR6-T23 | Criar componente `AnalysisPlaceholder`                          | —          | Placeholder para estados: loading (skeleton), indisponível, erro (com retry) |
| CR6-T24 | Criar componente `AnalysisFooter`                               | —          | Disclaimer + data + mês de referência                             |
| CR6-T25 | Adaptar `ScoreActions` para ações mescladas                     | CR6-T07, CR6-T16 | Componente aceita ações de ambas as fontes, exibe badge de dificuldade e economia |
| CR6-T26 | Reorganizar layout da aba Score                                 | CR6-T17 a CR6-T25 | Scroll único com 11 seções intercaladas conforme seção 7.2. Seções de IA respeitam regras de exibição da seção 7.3 |
| CR6-T27 | Testes de integração frontend                                   | CR6-T26    | Renderiza com dados mock (análise disponível, indisponível, loading, erro). Responsivo 320-1920px |
| CR6-T28 | Atualizar documentação (SPEC.md, PRD.md, ARCHITECTURE.md)       | CR6-T26    | Documentos refletem integração IA, prompt documentado, tabela de banco documentada |

---

## 12. Critérios de Aceite

| #  | Critério                                                                                  | Tipo       |
|----|-------------------------------------------------------------------------------------------|------------|
| 1  | DADO que o mês virou E existem dados suficientes do mês anterior QUANDO o usuário acessa a aba Score ENTÃO a análise é gerada automaticamente e as seções de IA são exibidas com dados | Funcional |
| 2  | DADO que a análise já foi gerada para o mês anterior QUANDO o usuário acessa a aba Score novamente ENTÃO a análise é carregada do cache (sem nova chamada de API) | Funcional |
| 3  | DADO que a análise está sendo gerada QUANDO as seções de IA são renderizadas ENTÃO exibem skeleton loading enquanto as seções de score (gauge, dimensões, evolução) renderizam instantaneamente | UX |
| 4  | DADO que a IA retorna o JSON da análise QUANDO o diagnóstico é renderizado ENTÃO exibe resumo geral, comparativo benchmark e pills de categorias com % da renda e variação colorida (verde=reduziu, vermelho=aumentou) | Funcional |
| 5  | DADO que a IA retorna alertas QUANDO a seção de alertas é renderizada ENTÃO os alertas aparecem ordenados por severidade (crítico primeiro) com ícone colorido e impacto em R$/mês e R$/ano | Funcional |
| 6  | DADO que existem ações da F04 E recomendações da IA QUANDO a seção "Como melhorar" é renderizada ENTÃO as ações são mescladas sem duplicação, ordenadas por impacto no score, limitadas a 5, com badge de dificuldade e economia estimada | Funcional |
| 7  | DADO que a IA detectou gastos recorrentes disfarçados de variáveis QUANDO a seção é renderizada ENTÃO exibe lista com descrição, frequência mensal, valor médio e sugestão | Funcional |
| 8  | DADO que a IA retorna metas QUANDO a seção é renderizada ENTÃO exibe 3 cards (curto/médio/longo) com descrição, valor-alvo, prazo e primeiro passo | Funcional |
| 9  | DADO que é o primeiro mês de uso (sem mês anterior fechado) QUANDO o usuário acessa a aba Score ENTÃO as seções de IA exibem placeholder "Sua primeira análise será gerada após o fechamento do mês" | Edge case |
| 10 | DADO que o mês anterior tem menos de 7 dias de registro E menos de 5 despesas planejadas QUANDO o usuário acessa a aba Score ENTÃO as seções de IA exibem "Dados insuficientes para análise" sem chamar API | Edge case |
| 11 | DADO que a chamada à API Claude falha (timeout, erro) QUANDO a análise é gerada ENTÃO as seções de IA exibem mensagem de erro com botão "Tentar novamente" | Erro |
| 12 | DADO que a IA retorna JSON malformado QUANDO o parsing é executado ENTÃO o sistema tenta reparar (fechar chaves/colchetes). Se falhar, exibe erro com retry. Log do JSON raw para debug | Erro |
| 13 | DADO que o score da F04 é 50 QUANDO a IA gera a análise ENTÃO o campo `score_saude_financeira` NÃO existe no output JSON (Opção B: IA não recalcula score) | Contrato |
| 14 | DADO que a IA retorna recomendação com `impacto_score_estimado: 5` QUANDO a seção "Como melhorar" é renderizada ENTÃO exibe "↑ ~5 pontos" ao lado da ação | Funcional |
| 15 | O endpoint GET `/api/analysis` responde em < 500ms quando retorna cache (análise já persistida) | Performance |
| 16 | A geração da análise completa (coleta + prompt + API + parsing + persistência) completa em < 30 segundos | Performance |
| 17 | O layout intercalado é responsivo de 320px a 1920px                                       | UI |
| 18 | A análise persistida inclui: JSON resultado, dados input (snapshot), tokens consumidos, modelo usado e tempo de processamento | Auditoria |

---

## 13. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                                        | Probabilidade | Mitigação                                                       |
|----|-----------------------------------------------------------------|---------------|-----------------------------------------------------------------|
| 1  | API Claude indisponível ou lenta                                | Baixa         | Timeout de 30s + 3 retries com backoff. Seções de score renderizam independente. Análise anterior permanece acessível |
| 2  | JSON da IA com campos ausentes ou formato inesperado            | Média         | Validação com Pydantic: campos obrigatórios com defaults. Log de JSONs problemáticos para ajustar prompt iterativamente |
| 3  | Custo de API acumula se muitos usuários                         | Baixa (MVP)   | MVP é single-user. Custo ~R$ 0,23/análise. Limite de 1/mês. Quando escalar, considerar cache agressivo e Haiku |
| 4  | IA gera recomendação que contradiz a ação da F04                | Média         | Merger prioriza IA e deduplica por dimensão. Se contradição direta, prevalece IA (mais contextualizada) |
| 5  | Análise se torna repetitiva mês a mês (mesmo diagnóstico)      | Alta          | Mitigação futura: incluir instrução delta-first no prompt ("foque no que mudou"). No MVP, aceitar repetição e validar se é percebida como problema |
| 6  | Prompt com dados demais excede janela de contexto               | Baixa         | Limitar gastos diários aos top 30 mais recentes por mês. Limitar histórico a 3 meses. Budget total: ~4K tokens input |
| 7  | Exposição da API key                                            | Baixa         | Key exclusivamente no backend (.env). Frontend nunca faz chamada direta à Anthropic |
| 8  | Seções de IA sem dados deixam a tela "vazia" no primeiro mês    | Alta          | Placeholder amigável com CTA: "Registre seus gastos durante o mês para receber sua primeira análise financeira completa" |

---

## 14. Fora de escopo (futuro)

| Item | Motivo |
|------|--------|
| Análise sob demanda (botão "Gerar nova análise") | Será implementada em CR futura. Botão ficará na seção de análise IA |
| Análise comparativa (mês a mês lado a lado) | Requer histórico. Evolução futura |
| Análise delta-first (foco em mudanças vs. repetir diagnóstico) | Validar primeiro se repetição é problema real |
| Compartilhamento da análise (exportar PDF, share) | Feature de engajamento para fase posterior |
| Notificação push "Sua análise mensal está pronta" | Depende de sistema de notificações (F05) |
| Integração com metas reais (vincular meta da IA a tracking) | Depende de F08 (Metas financeiras) |

---

## 15. Changelog

| Versão | Data       | Autor           | Descrição           |
|--------|------------|-----------------|---------------------|
| 1.0    | 2026-03-17 | Rafael Peixoto  | Criação do CR-006   |
