# Change Request — CR-005: Alertas e Notificações Inteligentes

**Versão:** 1.0  
**Data:** 2026-03-18  
**Status:** Concluído
**Autor:** Rafael Peixoto  
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Implementar sistema de alertas inteligentes in-app que transforma o MeuControle de passivo (usuário abre e descobre) para proativo (app avisa antes que o problema aconteça). O sistema inclui 8 tipos de alertas que consomem dados de todas as features já implementadas: despesas planejadas e categorias (F01), Dashboard (F02), projeção de parcelas (F03), score de saúde financeira (F04) e análise IA (F06). Os alertas são exibidos em 3 pontos: card no Dashboard, badge numérico na barra de navegação (visível de todas as abas), e banners inline nas abas contextuais. O motor de alertas é on-demand (calcula quando o usuário acessa o app), extensível (cada tipo é um checker independente), e o estado dos alertas (ativo/visto/dispensado) é persistido. Canal: in-app only (email e WhatsApp são extensões futuras).

---

## 2. Classificação

| Campo            | Valor                                                                 |
|------------------|-----------------------------------------------------------------------|
| Tipo             | Nova Feature (camada transversal)                                     |
| Origem           | Roadmap F05 (Benchmark competitivo + evolução do produto)             |
| Urgência         | Próxima sprint                                                        |
| Complexidade     | Média                                                                 |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

O MeuControle possui:
- Despesas planejadas com status Pago/Pendente/Atrasado (regra: despesas vencidas não pagas viram "Atrasado")
- Categorização em despesas planejadas e gastos diários (F01)
- Dashboard com gráficos e indicadores (F02)
- Visão consolidada de parcelas futuras com projeção (F03)
- Score de saúde financeira com breakdown e evolução (F04)
- Análise financeira mensal por IA com alertas, recomendações e metas (F06)

O app não tem **nenhum mecanismo proativo**. Não avisa que uma despesa vence amanhã, não avisa que uma parcela está terminando, não avisa que o score caiu. O usuário precisa abrir cada aba e interpretar visualmente. Com 25+ despesas por mês com vencimentos espalhados entre o dia 1 e o dia 28, gerenciar tudo mentalmente é inviável.

### Problema ou Necessidade

1. **Nenhum alerta de vencimento**: despesas vencem e viram "Atrasado" sem aviso prévio. No Brasil, boletos têm multa de 2% + juros diários por atraso, e rotativo de cartão cobra 15%+/mês.
2. **Oportunidades invisíveis**: parcelas terminam e o dinheiro liberado não é destacado como oportunidade de realocação. O usuário pode nem perceber que uma parcela de R$ 511/mês acabou.
3. **Análise IA gera alertas que morrem no JSON**: a F06 produz alertas detalhados (crítico/atenção/informativo) mas eles só aparecem na aba Score, dentro da análise. Não há promoção para um sistema unificado.
4. **Score deteriora silenciosamente**: uma queda de 15 pontos no score (como a variação visível na tela atual: -15 vs. mês anterior) deveria gerar um alerta proativo, não depender do usuário notar.

### Situação Desejada (TO-BE)

Sistema de alertas com:
- 8 tipos de alertas (6 determinísticos + 2 derivados da IA)
- 3 pontos de exibição: card no Dashboard, badge na navegação, banners inline
- Motor extensível on-demand
- Estado persistido (ativo/visto/dispensado)
- Configurações do usuário para personalizar antecedência e tipos

---

## 4. Catálogo de Alertas

### Grupo 1 — Alertas determinísticos (calculados localmente)

| ID | Nome | Gatilho | Severidade | Dados consumidos |
|----|------|---------|------------|------------------|
| A1 | Vencimento próximo | Despesa com status "Pendente" vence em X dias (configurável: 1/3/5/7) | Atenção | Despesas planejadas (vencimento, status) |
| A2 | Despesa atrasada | Despesa com data de vencimento < hoje E status ≠ "Pago" | Crítico | Despesas planejadas (vencimento, status) |
| A3 | Parcela encerrando | Parcela nas últimas 2 prestações (X ≥ Y-1 de Y) | Informativo | Parcelas (F03) |
| A4 | Score deteriorando | Score do mês atual < score mês anterior em ≥ 5 pontos | Atenção | Score histórico (F04) |
| A5 | Comprometimento alto | % de comprometimento da renda com fixos > limiar (default: 50%) | Atenção | Despesas planejadas + Receitas |
| A6 | Parcela pendente ativada | Parcela muda de "0 de Y" para "1 de Y" (detectado na virada do mês) | Crítico | Parcelas (F03) |

### Grupo 2 — Alertas derivados da análise IA (F06)

| ID | Nome | Gatilho | Severidade | Dados consumidos |
|----|------|---------|------------|------------------|
| A7 | Alerta da análise IA | Análise mensal gerada com alertas no JSON (tipo: crítico/atenção/informativo) | Varia (do JSON) | analise_financeira.resultado.alertas |
| A8 | Gasto recorrente disfarçado | Análise IA detecta variável que aparece todo mês | Informativo | analise_financeira.resultado.gastos_recorrentes_disfarcados |

### Detalhamento de cada alerta

**A1: Vencimento próximo**

```
Título:   "[Nome da despesa] vence em [X] dias"
Descrição: "R$ [valor] com vencimento em [data]. Fonte: [fonte de pagamento]."
Ação:      Botão "Marcar como pago" (atualiza status direto do alerta)
Exemplo:   "IPVA vence em 3 dias — R$ 1.034,58 com vencimento em 19/02. Fonte: Salário Koin."
```

Regras:
- Gera 1 alerta por despesa pendente dentro do período de antecedência
- Não gera para despesas já pagas
- Recalcula toda vez que o endpoint é chamado (sempre atualizado)
- Antecedência configurável pelo usuário (default: 3 dias)

**A2: Despesa atrasada**

```
Título:   "[Nome da despesa] está atrasada"
Descrição: "Venceu em [data] ([X] dias atrás). Valor: R$ [valor]."
Ação:      Botão "Marcar como pago"
Exemplo:   "Conta de luz está atrasada — Venceu em 10/02 (8 dias atrás). R$ 291,84."
```

Regras:
- Severidade: Crítico (sempre)
- Aparece até que a despesa seja marcada como paga ou dispensada
- Se múltiplas atrasadas, todas aparecem ordenadas por dias de atraso (mais atrasada primeiro)

**A3: Parcela encerrando**

```
Título:   "[Nome da parcela] termina [este mês | no próximo mês]"
Descrição: "Parcela [X de Y]. R$ [valor]/mês será liberado a partir de [mês seguinte]."
Ação:      Link "Ver parcelas" (navega para aba Parcelas)
Exemplo:   "Seguro do Carro termina este mês — Parcela 10 de 10. R$ 511,80/mês livre a partir de abril."
```

Regras:
- Gera quando parcela_atual ≥ (parcela_total - 1), ou seja, penúltima ou última
- Severidade: Informativo (é oportunidade, não problema)
- Inclui valor que será liberado (conecta com F03)

**A4: Score deteriorando**

```
Título:   "Seu score caiu [X] pontos"
Descrição: "De [score_anterior] para [score_atual]. Principal motivo: [dimensão com maior queda]."
Ação:      Link "Ver detalhes" (navega para aba Score)
Exemplo:   "Seu score caiu 15 pontos — De 65 (Saudável) para 50 (Estável). Principal motivo: capacidade de poupança reduziu."
```

Regras:
- Gera quando score_atual < score_mes_anterior em ≥ 5 pontos
- Identificar a dimensão (D1-D4) que mais contribuiu para a queda
- 1 alerta por mês (não recalcula a cada acesso, usa snapshot salvo na F04)
- Também gera alerta positivo quando score sobe ≥ 10 pontos (tipo: informativo, tom: "Seu score subiu 12 pontos! Bom trabalho.")

**A5: Comprometimento alto**

```
Título:   "Comprometimento com fixos acima de [limiar]%"
Descrição: "Gastos fixos consomem [X]% da renda ([ideal: até [limiar]%]). Diferença: R$ [excedente]/mês."
Ação:      Link "Ver recomendações" (navega para aba Score, seção Como Melhorar)
Exemplo:   "Comprometimento com fixos acima de 50% — 69,5% da renda comprometida (ideal: até 50%). Excedente: R$ 3.437/mês."
```

Regras:
- Alerta permanente enquanto indicador estiver acima do limiar
- Limiar configurável pelo usuário (default: 50%)
- Recalcula a cada acesso com dados atuais do mês

**A6: Parcela pendente ativada**

```
Título:   "[Nome] iniciou pagamento"
Descrição: "Nova parcela de R$ [valor]/mês por [Y] meses. Comprometimento subiu para [X]%."
Ação:      Link "Ver impacto" (navega para aba Parcelas, projeção)
Exemplo:   "Empr. Itaú iniciou pagamento — R$ 2.726,52/mês por 60 meses. Comprometimento subiu para 79,6%."
```

Regras:
- Detecta parcelas que no mês anterior eram "0 de Y" e agora são "1 de Y"
- Severidade: Crítico (mudança significativa no orçamento)
- Inclui impacto no percentual de comprometimento

**A7: Alertas da análise IA**

```
Título:   [titulo do JSON da F06]
Descrição: [descricao do JSON da F06]
Severidade: [tipo do JSON: critico → Crítico, atencao → Atenção, informativo → Informativo]
Ação:      Link "Ver análise" (navega para aba Score, seção de análise IA)
```

Regras:
- Promovidos do JSON `analise_financeira.resultado.alertas` quando a análise mensal é gerada
- Mantêm severidade original da IA
- Persistidos com referência ao ID da análise
- Máximo 5 (limite já definido na F06)

**A8: Gasto recorrente disfarçado**

```
Título:   "[Descrição] aparece [X]x por mês"
Descrição: "Média de R$ [valor]/mês. Considere incluir como gasto planejado para melhor controle."
Ação:      Botão "Criar gasto planejado" (pré-preenche formulário com dados do alerta)
Exemplo:   "iFood aparece 18x por mês — Média de R$ 890/mês. Considere incluir como gasto planejado."
```

Regras:
- Promovidos do JSON `analise_financeira.resultado.gastos_recorrentes_disfarcados`
- Severidade: Informativo
- Ação diferenciada: permite criar gasto planejado direto do alerta

---

## 5. Pontos de Exibição

### 5.1 Card no Dashboard (F02)

Novo card adicionado ao Dashboard existente:

```
┌──────────────────────────────────────────┐
│ 🔔 Alertas                       3 novos │
│                                          │
│ 🔴 Conta de luz está atrasada           │
│    Venceu em 10/03 (8 dias atrás)       │
│                          [Marcar pago]   │
│                                          │
│ 🟡 IPVA vence em 3 dias                 │
│    R$ 1.034,58 — vencimento 19/03       │
│                          [Marcar pago]   │
│                                          │
│ 🔵 Seguro do Carro termina este mês     │
│    R$ 511,80/mês livre a partir de abril │
│                                          │
│              Ver todos (7) →             │
└──────────────────────────────────────────┘
```

Regras do card:
- Exibe no máximo 3 alertas (os mais urgentes/severos)
- Ordenação: Crítico primeiro → Atenção → Informativo. Dentro da mesma severidade, mais recente primeiro
- Link "Ver todos (N)" abre modal ou seção expandida com lista completa
- Se nenhum alerta ativo: card exibe "Tudo em dia! Nenhum alerta no momento." com ícone ✅
- Ação rápida "Marcar como pago" disponível direto no card para alertas A1 e A2

### 5.2 Badge na barra de navegação

Badge numérico (bolinha vermelha) visível em todas as abas do app:

```
Dashboard    Gastos Planejados    Gastos Diários    Parcelas    Score
                                                                  🔴3
```

Regras:
- Número = quantidade de alertas com status "ativo" (não vistos/dispensados)
- Badge posicionado sobre o item "Dashboard" na navegação (ponto de acesso principal dos alertas)
- Cor: vermelho se algum alerta é Crítico, amarelo se apenas Atenção/Informativo
- Desaparece quando todos os alertas são vistos ou dispensados
- Atualiza a cada navegação entre abas (recalcula no endpoint)

### 5.3 Banners inline nas abas contextuais

Banners sutis no topo das abas relevantes, apenas para alertas diretamente relacionados à aba:

**Aba Gastos Planejados:**
```
┌──────────────────────────────────────────┐
│ ⚠️ 2 despesas atrasadas, 3 vencem esta  │
│ semana                    [Ver alertas]  │
└──────────────────────────────────────────┘
```

**Aba Parcelas:**
```
┌──────────────────────────────────────────┐
│ ℹ️ Seguro do Carro termina este mês.    │
│ R$ 511,80/mês será liberado      [Ver]  │
└──────────────────────────────────────────┘
```

**Aba Score:**
```
┌──────────────────────────────────────────┐
│ ⚠️ Score caiu 15 pontos vs. mês         │
│ anterior                  [Ver detalhes] │
└──────────────────────────────────────────┘
```

Regras:
- Máximo 1 banner por aba (o mais relevante/severo)
- Banner é dismissable (X para fechar, marca como "visto")
- Background sutil: vermelho claro (crítico), amarelo claro (atenção), azul claro (informativo)
- Não aparece se todos os alertas da aba estão vistos/dispensados

---

## 6. Ciclo de vida do alerta

```
                  ┌─────────┐
                  │  Gerado │
                  └────┬────┘
                       │
                       ▼
                  ┌─────────┐
           ┌──────│  Ativo  │──────┐
           │      └────┬────┘      │
           │           │           │
     Usuário viu  Usuário agiu  Usuário dispensou
     (abriu card) (marcou pago)  (clicou dismiss)
           │           │           │
           ▼           ▼           ▼
      ┌─────────┐ ┌──────────┐ ┌─────────────┐
      │  Visto  │ │ Resolvido│ │ Dispensado   │
      └─────────┘ └──────────┘ └─────────────┘
           │
           │ (ainda aparece, sem badge)
           │
     Usuário dispensa
           │
           ▼
      ┌─────────────┐
      │ Dispensado   │
      └─────────────┘
```

| Status | Badge conta? | Aparece no card? | Aparece no banner? |
|--------|-------------|-----------------|-------------------|
| Ativo | Sim | Sim | Sim |
| Visto | Não | Sim (sem destaque "novo") | Não |
| Resolvido | Não | Não | Não |
| Dispensado | Não | Não | Não |

**Resolução automática:**
- A1 (vencimento próximo) → resolvido quando despesa marcada como paga
- A2 (atrasada) → resolvido quando despesa marcada como paga
- A3 (parcela encerrando) → resolvido quando mês vira e parcela termina
- A4 (score deteriorando) → resolvido no mês seguinte (novo cálculo)
- A5 (comprometimento alto) → resolvido quando % cai abaixo do limiar
- A6 (parcela ativada) → resolvido quando alerta é visto (informação one-time)
- A7/A8 (IA) → resolvido na próxima análise mensal (novos alertas substituem)

---

## 7. Configurações do usuário

Nova seção em Configurações (ou modal acessível via ícone ⚙️ no card de alertas):

| Configuração | Default | Opções | Persistência |
|-------------|---------|--------|-------------|
| Antecedência de vencimento (A1) | 3 dias | 1, 3, 5, 7 dias | `configuracao_alertas.antecedencia_vencimento` |
| Alertar despesas atrasadas (A2) | Ligado | Ligado / Desligado | `configuracao_alertas.alerta_atrasadas` |
| Alertar parcelas encerrando (A3) | Ligado | Ligado / Desligado | `configuracao_alertas.alerta_parcelas_encerrando` |
| Alertar variação de score (A4) | Ligado | Ligado / Desligado | `configuracao_alertas.alerta_score` |
| Alertar comprometimento alto (A5) | Ligado | Ligado / Desligado | `configuracao_alertas.alerta_comprometimento` |
| Limiar de comprometimento (A5) | 50% | 40%, 50%, 60%, 70% | `configuracao_alertas.limiar_comprometimento` |
| Alertar parcela pendente ativada (A6) | Ligado | Ligado / Desligado | `configuracao_alertas.alerta_parcela_ativada` |
| Mostrar alertas da análise IA (A7/A8) | Ligado | Ligado / Desligado | `configuracao_alertas.alerta_ia` |

---

## 8. Detalhamento da Mudança

### 8.1 O que muda

| #  | Item                              | Antes (AS-IS)                                        | Depois (TO-BE)                                                                      |
|----|-----------------------------------|------------------------------------------------------|-------------------------------------------------------------------------------------|
| 1  | Proatividade do app               | 100% passivo (usuário descobre ao abrir)             | Proativo: alertas calculados e exibidos automaticamente                              |
| 2  | Dashboard (F02)                   | Gráficos + indicadores + card score                  | Adiciona card de alertas com preview + ações rápidas                                |
| 3  | Barra de navegação               | Tabs sem indicadores                                 | Badge numérico sobre "Dashboard" com contagem de alertas ativos                     |
| 4  | Aba Gastos Planejados            | Tabela de despesas                                   | Adiciona banner inline no topo para despesas atrasadas/vencendo                     |
| 5  | Aba Parcelas                     | Projeção + tabela de parcelas                        | Adiciona banner inline para parcelas encerrando                                     |
| 6  | Aba Score                        | Score + análise IA                                   | Adiciona banner inline para variação de score                                       |
| 7  | Alertas da análise IA (F06)      | Vivem apenas dentro da seção de análise na aba Score | Promovidos para o sistema unificado de alertas (card Dashboard + badge)              |
| 8  | Status "Atrasado" de despesas    | Existe como status visual na tabela                  | Gera alerta ativo com ação rápida "Marcar como pago"                                |
| 9  | Configurações                    | Não existem configurações de alertas                 | Nova seção de configurações com 8 opções                                            |

### 8.2 O que NÃO muda

- Modelo de dados de despesas planejadas, gastos diários, parcelas
- Regra de negócio existente (status "Atrasado" para despesas vencidas)
- Tela de Score (F04 + F06): seções internas de análise IA continuam iguais
- Dashboard (F02): cards existentes não são alterados, apenas novo card adicionado
- Cálculo do score (F04) e geração da análise IA (F06) permanecem iguais
- Não há notificações externas (email, push, WhatsApp) nesta CR

---

## 9. Impacto nos Documentos

| Documento                          | Impactado? | Seções Afetadas                        | Ação Necessária                                   |
|------------------------------------|------------|----------------------------------------|---------------------------------------------------|
| `/docs/PRD.md`                     | Sim        | Requisitos Funcionais                  | Adicionar RF para sistema de alertas               |
| `/docs/ARCHITECTURE.md`            | Sim        | Modelagem de Dados, Estrutura de Pastas | Adicionar tabelas, documentar motor de alertas    |
| `/docs/SPEC.md`                    | Sim        | Features, Endpoints, Componentes UI    | Detalhar módulo de alertas completo                |
| `/docs/IMPLEMENTATION_PLAN.md`     | Sim        | Adicionar novo grupo de tarefas        | Inserir tarefas da F05                             |

---

## 10. Impacto no Código

### 10.1 Arquivos Afetados

| Ação      | Caminho (estimado)                                            | Descrição                                                     |
|-----------|---------------------------------------------------------------|---------------------------------------------------------------|
| Criar     | `backend/services/alerts/alert_engine.py`                     | Motor de alertas: orquestra a execução de todos os checkers    |
| Criar     | `backend/services/alerts/checkers/vencimento_proximo.py`      | Checker A1: despesas pendentes vencendo em X dias              |
| Criar     | `backend/services/alerts/checkers/despesa_atrasada.py`        | Checker A2: despesas vencidas não pagas                        |
| Criar     | `backend/services/alerts/checkers/parcela_encerrando.py`      | Checker A3: parcelas nas últimas 2 prestações                  |
| Criar     | `backend/services/alerts/checkers/score_deteriorando.py`      | Checker A4: queda ≥ 5 pontos no score                         |
| Criar     | `backend/services/alerts/checkers/comprometimento_alto.py`    | Checker A5: fixos > limiar da renda                            |
| Criar     | `backend/services/alerts/checkers/parcela_ativada.py`         | Checker A6: parcela mudou de 0/Y para 1/Y                     |
| Criar     | `backend/services/alerts/checkers/alertas_ia.py`              | Checker A7+A8: promove alertas do JSON da F06                  |
| Criar     | `backend/services/alerts/alert_state.py`                      | Gerenciador de estado: ativo/visto/dispensado, resolução automática |
| Criar     | `backend/schemas/alerts.py`                                   | Schemas Pydantic para alertas                                  |
| Criar     | `backend/routes/alerts.py`                                    | Endpoints: GET /api/alerts, PATCH /api/alerts/{id}/dismiss, PATCH /api/alerts/{id}/seen |
| Criar     | `backend/models/alerta_estado.py`                             | Modelo ORM para tabela `alerta_estado`                         |
| Criar     | `backend/models/configuracao_alertas.py`                      | Modelo ORM para tabela `configuracao_alertas`                  |
| Modificar | `backend/routes/__init__.py` (ou equivalente)                 | Registrar novas rotas                                          |
| Criar     | `frontend/src/components/alerts/AlertsCard.tsx`               | Card de alertas para Dashboard (preview de 3 + "ver todos")    |
| Criar     | `frontend/src/components/alerts/AlertItem.tsx`                | Componente individual de alerta (ícone, título, descrição, ação) |
| Criar     | `frontend/src/components/alerts/AlertsList.tsx`               | Lista completa de alertas (modal ou seção expandida)            |
| Criar     | `frontend/src/components/alerts/AlertBanner.tsx`              | Banner inline para abas contextuais                             |
| Criar     | `frontend/src/components/alerts/AlertBadge.tsx`               | Badge numérico para barra de navegação                          |
| Criar     | `frontend/src/components/alerts/AlertsSettings.tsx`           | Modal/seção de configurações de alertas                         |
| Modificar | `frontend/src/pages/Dashboard.tsx` (ou equivalente)           | Adicionar AlertsCard ao layout do Dashboard                     |
| Modificar | `frontend/src/components/layout/Navigation.tsx` (ou equivalente) | Adicionar AlertBadge ao item "Dashboard" na navegação        |
| Modificar | `frontend/src/pages/GastosplanejadosPage.tsx` (ou equivalente) | Adicionar AlertBanner para A1/A2                              |
| Modificar | `frontend/src/pages/Parcelas.tsx` (ou equivalente)            | Adicionar AlertBanner para A3/A6                               |
| Modificar | `frontend/src/pages/Score.tsx` (ou equivalente)               | Adicionar AlertBanner para A4                                   |
| Criar     | `frontend/src/hooks/useAlerts.ts`                             | Hook para consumir endpoints de alertas                         |
| Criar     | `frontend/src/types/alerts.ts`                                | Types TypeScript para alertas                                   |
| Criar     | `backend/tests/test_alert_engine.py`                          | Testes do motor de alertas (orquestração)                       |
| Criar     | `backend/tests/test_checkers/`                                | Testes unitários de cada checker (A1-A8)                        |
| Criar     | `backend/tests/test_alert_state.py`                           | Testes de gerenciamento de estado                               |

### 10.2 Banco de Dados

| Ação   | Descrição                                              | Migration Necessária? |
|--------|-------------------------------------------------------|-----------------------|
| Criar  | Tabela `alerta_estado` para persistir estado dos alertas | Sim                |
| Criar  | Tabela `configuracao_alertas` para preferências         | Sim                |

**Migrations:**

```sql
-- Tabela de estado dos alertas
CREATE TABLE alerta_estado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alerta_tipo VARCHAR(10) NOT NULL,
    alerta_referencia VARCHAR(100) NOT NULL,
    mes_referencia DATE NOT NULL,
    severidade VARCHAR(20) NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    descricao VARCHAR(300),
    dados_extra JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'ativo',
    visto_em TIMESTAMP,
    dispensado_em TIMESTAMP,
    resolvido_em TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alerta_tipo, alerta_referencia, mes_referencia)
);

CREATE INDEX idx_alerta_status ON alerta_estado(status);
CREATE INDEX idx_alerta_mes ON alerta_estado(mes_referencia);

-- Tabela de configurações de alertas
CREATE TABLE configuracao_alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    antecedencia_vencimento INTEGER NOT NULL DEFAULT 3,
    alerta_atrasadas BOOLEAN NOT NULL DEFAULT TRUE,
    alerta_parcelas_encerrando BOOLEAN NOT NULL DEFAULT TRUE,
    alerta_score BOOLEAN NOT NULL DEFAULT TRUE,
    alerta_comprometimento BOOLEAN NOT NULL DEFAULT TRUE,
    limiar_comprometimento INTEGER NOT NULL DEFAULT 50,
    alerta_parcela_ativada BOOLEAN NOT NULL DEFAULT TRUE,
    alerta_ia BOOLEAN NOT NULL DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir configuração default
INSERT INTO configuracao_alertas DEFAULT VALUES;
```

---

## 11. Motor de Alertas: Arquitetura extensível

### Interface do checker

```python
# backend/services/alerts/base_checker.py
from abc import ABC, abstractmethod
from typing import List
from schemas.alerts import AlertaOutput

class BaseAlertChecker(ABC):
    """Interface base para checkers de alerta."""
    
    @property
    @abstractmethod
    def tipo(self) -> str:
        """Identificador do tipo de alerta (ex: 'A1', 'A2')"""
        pass
    
    @abstractmethod
    def check(self, dados: dict, config: dict) -> List[AlertaOutput]:
        """
        Verifica condições e retorna lista de alertas.
        
        Args:
            dados: dicionário com dados financeiros agregados
            config: configurações do usuário para alertas
        
        Returns:
            Lista de alertas gerados (pode ser vazia)
        """
        pass
```

### Motor de alertas (orquestrador)

```python
# backend/services/alerts/alert_engine.py
class AlertEngine:
    def __init__(self):
        self.checkers: List[BaseAlertChecker] = [
            VencimentoProximoChecker(),    # A1
            DespesaAtrasadaChecker(),      # A2
            ParcelaEncerrandoChecker(),    # A3
            ScoreDeteriorandoChecker(),    # A4
            ComprometimentoAltoChecker(),  # A5
            ParcelaAtivadaChecker(),       # A6
            AlertasIAChecker(),            # A7 + A8
        ]
    
    def calcular_alertas(self, dados: dict, config: dict) -> List[AlertaOutput]:
        alertas = []
        for checker in self.checkers:
            if self._checker_habilitado(checker, config):
                alertas.extend(checker.check(dados, config))
        
        # Ordenar: Crítico > Atenção > Informativo, depois por data
        alertas.sort(key=lambda a: (
            {'critico': 0, 'atencao': 1, 'informativo': 2}[a.severidade],
            a.created_at
        ))
        
        return alertas
    
    def _checker_habilitado(self, checker, config) -> bool:
        """Verifica se o checker está habilitado nas configurações."""
        mapping = {
            'A1': config.get('antecedencia_vencimento', 3) > 0,
            'A2': config.get('alerta_atrasadas', True),
            'A3': config.get('alerta_parcelas_encerrando', True),
            'A4': config.get('alerta_score', True),
            'A5': config.get('alerta_comprometimento', True),
            'A6': config.get('alerta_parcela_ativada', True),
            'A7': config.get('alerta_ia', True),
            'A8': config.get('alerta_ia', True),
        }
        return mapping.get(checker.tipo, True)
```

Para adicionar novo tipo de alerta no futuro: criar novo checker implementando `BaseAlertChecker`, registrar no `AlertEngine.__init__`, e adicionar configuração na tabela.

---

## 12. Estrutura de resposta do endpoint

### GET /api/alerts

```json
{
  "alertas": [
    {
      "id": 1,
      "tipo": "A2",
      "severidade": "critico",
      "titulo": "Conta de luz está atrasada",
      "descricao": "Venceu em 10/03 (8 dias atrás). Valor: R$ 291,84.",
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
    },
    {
      "id": 2,
      "tipo": "A1",
      "severidade": "atencao",
      "titulo": "IPVA vence em 3 dias",
      "descricao": "R$ 1.034,58 com vencimento em 19/03. Fonte: Salário Koin.",
      "impacto_mensal": 1034.58,
      "impacto_anual": null,
      "status": "ativo",
      "acao": {
        "tipo": "marcar_pago",
        "label": "Marcar como pago",
        "referencia_id": 78
      },
      "contexto_aba": "gastos_planejados",
      "created_at": "2026-03-16T08:00:00Z"
    },
    {
      "id": 3,
      "tipo": "A3",
      "severidade": "informativo",
      "titulo": "Seguro do Carro termina este mês",
      "descricao": "Parcela 10 de 10. R$ 511,80/mês livre a partir de abril.",
      "impacto_mensal": 511.80,
      "impacto_anual": 6141.60,
      "status": "ativo",
      "acao": {
        "tipo": "navegar",
        "label": "Ver parcelas",
        "destino": "/parcelas"
      },
      "contexto_aba": "parcelas",
      "created_at": "2026-03-01T08:00:00Z"
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

### PATCH /api/alerts/{id}/seen

```json
{ "status": "visto", "visto_em": "2026-03-18T10:30:00Z" }
```

### PATCH /api/alerts/{id}/dismiss

```json
{ "status": "dispensado", "dispensado_em": "2026-03-18T10:31:00Z" }
```

### GET /api/alerts/config

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

### PUT /api/alerts/config

Mesmo body do GET, atualiza configurações.

---

## 13. Tarefas de Implementação

| ID      | Tarefa                                                          | Depende de | Done When                                                        |
|---------|-----------------------------------------------------------------|------------|------------------------------------------------------------------|
| CR5-T01 | Criar migrations (alerta_estado + configuracao_alertas)         | —          | Tabelas criadas, migration reversível, config default inserida   |
| CR5-T02 | Criar modelos ORM                                               | CR5-T01    | Modelos mapeados com CRUD funcional                              |
| CR5-T03 | Criar interface BaseAlertChecker                                | —          | Classe abstrata com contrato de tipo + check()                   |
| CR5-T04 | Criar checker A1 (vencimento próximo)                           | CR5-T03    | Retorna alertas para despesas pendentes dentro da antecedência configurada |
| CR5-T05 | Criar checker A2 (despesa atrasada)                             | CR5-T03    | Retorna alertas para despesas vencidas não pagas, com dias de atraso |
| CR5-T06 | Criar checker A3 (parcela encerrando)                           | CR5-T03    | Retorna alertas para parcelas com atual ≥ total-1, com valor liberado |
| CR5-T07 | Criar checker A4 (score deteriorando)                           | CR5-T03    | Retorna alerta quando score caiu ≥ 5 pts, identifica dimensão. Também gera positivo quando sobe ≥ 10 |
| CR5-T08 | Criar checker A5 (comprometimento alto)                         | CR5-T03    | Retorna alerta quando fixos > limiar configurado, com excedente em R$ |
| CR5-T09 | Criar checker A6 (parcela pendente ativada)                     | CR5-T03    | Detecta parcelas que mudaram de 0/Y para 1/Y, com impacto no comprometimento |
| CR5-T10 | Criar checker A7+A8 (alertas IA)                                | CR5-T03    | Promove alertas e gastos recorrentes do JSON da última análise F06 |
| CR5-T11 | Criar AlertEngine (orquestrador)                                | CR5-T04 a CR5-T10 | Executa todos os checkers habilitados, ordena por severidade, retorna lista |
| CR5-T12 | Criar gerenciador de estado (alert_state)                       | CR5-T02    | Gerencia transições ativo→visto→dispensado, resolução automática por tipo |
| CR5-T13 | Criar schemas Pydantic                                          | —          | Schemas para alertas, resumo, config                              |
| CR5-T14 | Criar endpoints (GET /alerts, PATCH dismiss/seen, GET/PUT config) | CR5-T11, CR5-T12, CR5-T13 | Endpoints funcionais retornando alertas com estado e ações |
| CR5-T15 | Testes unitários de cada checker                                | CR5-T04 a CR5-T10 | Cenários: alertas gerados, nenhum alerta, edge cases (0 despesas, 0 parcelas, primeiro mês) |
| CR5-T16 | Testes do motor e gerenciador de estado                         | CR5-T11, CR5-T12 | Orquestração correta, checkers desabilitados respeitados, transições de estado funcionam |
| CR5-T17 | Criar types TypeScript                                          | CR5-T13    | Types refletem schemas do backend                                |
| CR5-T18 | Criar hook useAlerts                                            | CR5-T17    | Hook consome endpoints, retorna alertas + resumo + config + mutations (dismiss, seen, updateConfig) |
| CR5-T19 | Criar componente AlertItem                                      | CR5-T18    | Ícone de severidade + título + descrição + ação + dismiss. Variante compacta (card) e expandida (lista) |
| CR5-T20 | Criar componente AlertsCard                                     | CR5-T19    | Card para Dashboard: preview 3 alertas, resumo, "ver todos". Estado vazio: "Tudo em dia!" |
| CR5-T21 | Criar componente AlertsList                                     | CR5-T19    | Lista completa de alertas em modal ou seção expandida             |
| CR5-T22 | Criar componente AlertBadge                                     | CR5-T18    | Badge numérico com cor (vermelho/amarelo) baseada na maior severidade |
| CR5-T23 | Criar componente AlertBanner                                    | CR5-T18    | Banner inline para abas contextuais, dismissable                  |
| CR5-T24 | Criar componente AlertsSettings                                 | CR5-T18    | Modal/seção de configurações com toggles e selects                |
| CR5-T25 | Integrar AlertsCard no Dashboard                                | CR5-T20    | Card adicionado ao layout, posição adequada entre cards existentes |
| CR5-T26 | Integrar AlertBadge na navegação                                | CR5-T22    | Badge visível no item "Dashboard", atualiza a cada navegação      |
| CR5-T27 | Integrar AlertBanner nas abas                                   | CR5-T23    | Banner no topo de Gastos Planejados (A1/A2), Parcelas (A3/A6), Score (A4) |
| CR5-T28 | Implementar ação "Marcar como pago" direto do alerta            | CR5-T19    | Botão no AlertItem chama endpoint de atualizar despesa, resolve alerta |
| CR5-T29 | Implementar ação "Criar gasto planejado" (A8)                   | CR5-T19    | Botão no AlertItem abre formulário pré-preenchido com dados do gasto recorrente |
| CR5-T30 | Testes de integração frontend                                   | CR5-T27    | Renderiza em todos os cenários (com alertas, sem alertas, loading, erro). Responsivo 320-1920px |
| CR5-T31 | Atualizar documentação (SPEC.md, PRD.md, ARCHITECTURE.md)       | CR5-T27    | Documentos refletem sistema de alertas, catálogo documentado      |

---

## 14. Critérios de Aceite

| #  | Critério                                                                                  | Tipo       |
|----|-------------------------------------------------------------------------------------------|------------|
| 1  | DADO que existe despesa pendente vencendo em 3 dias (default) QUANDO o usuário acessa o app ENTÃO alerta A1 aparece no card do Dashboard com título, valor e botão "Marcar como pago" | Funcional |
| 2  | DADO que existe despesa vencida há 5 dias com status ≠ Pago QUANDO alertas são calculados ENTÃO alerta A2 (crítico) aparece com dias de atraso e ação "Marcar como pago" | Funcional |
| 3  | DADO que o usuário clica "Marcar como pago" no alerta QUANDO a ação é executada ENTÃO a despesa é atualizada para status "Pago" E o alerta é resolvido automaticamente | Funcional |
| 4  | DADO que uma parcela está na prestação 9 de 10 QUANDO alertas são calculados ENTÃO alerta A3 aparece com valor mensal que será liberado e mês de liberação | Funcional |
| 5  | DADO que o score caiu de 65 para 50 (queda de 15 pontos) QUANDO alertas são calculados ENTÃO alerta A4 aparece identificando a dimensão com maior queda | Funcional |
| 6  | DADO que o score subiu de 50 para 62 (subida de 12 pontos) QUANDO alertas são calculados ENTÃO alerta A4 informativo aparece com mensagem positiva | Funcional |
| 7  | DADO comprometimento de fixos em 69,5% e limiar configurado em 50% QUANDO alertas são calculados ENTÃO alerta A5 permanente aparece com excedente em R$ | Funcional |
| 8  | DADO que a análise IA (F06) gerou 3 alertas no JSON QUANDO alertas são calculados ENTÃO alertas A7 aparecem com severidade e texto originais da IA | Funcional |
| 9  | DADO que existem 7 alertas ativos QUANDO o usuário visualiza a barra de navegação ENTÃO badge mostra "7" com cor vermelha (há pelo menos 1 crítico) | UI |
| 10 | DADO que o usuário abre o card de alertas no Dashboard QUANDO há 7 alertas ENTÃO exibe os 3 mais urgentes com link "Ver todos (7)" | UI |
| 11 | DADO que o usuário dispensa um alerta QUANDO o endpoint dismiss é chamado ENTÃO o alerta não aparece mais no card, lista ou banner, e badge decrementa | Funcional |
| 12 | DADO que o usuário configura antecedência para 7 dias QUANDO alertas A1 são calculados ENTÃO despesas vencendo em até 7 dias geram alertas | Config |
| 13 | DADO que o usuário desabilita alertas de parcelas encerrando QUANDO alertas são calculados ENTÃO nenhum alerta A3 é gerado | Config |
| 14 | DADO que o usuário acessa a aba Gastos Planejados QUANDO existem despesas atrasadas ENTÃO banner inline aparece no topo com contagem e link | UI |
| 15 | DADO que não existem alertas ativos QUANDO o card de alertas é renderizado ENTÃO exibe "Tudo em dia!" com ícone ✅ | Edge case |
| 16 | DADO que é o primeiro mês de uso (sem score anterior) QUANDO alerta A4 é avaliado ENTÃO não gera alerta (sem base de comparação) | Edge case |
| 17 | DADO que não existe análise IA (F06) para o mês QUANDO alertas A7/A8 são avaliados ENTÃO nenhum alerta de IA é gerado | Edge case |
| 18 | O endpoint GET /api/alerts responde em < 500ms                                            | Performance |
| 19 | O layout é responsivo de 320px a 1920px                                                   | UI |

---

## 15. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                                        | Probabilidade | Mitigação                                                       |
|----|-----------------------------------------------------------------|---------------|-----------------------------------------------------------------|
| 1  | Excesso de alertas causa "alert fatigue" (usuário ignora todos) | Média         | Limite visual: max 3 no card, max 1 banner por aba. Configurações permitem desabilitar tipos. Severidade garante que críticos se destacam |
| 2  | Ação "Marcar como pago" direto do alerta pode causar marcação acidental | Baixa   | Confirmar com feedback visual ("Despesa marcada como paga ✓") + opção de desfazer (undo) por 5 segundos |
| 3  | Alertas A7/A8 da IA podem conter texto longo ou mal formatado   | Média         | Limites de caracteres já definidos na F06 (60 chars título, 200 chars descrição). Truncar com "..." se exceder |
| 4  | Motor de alertas adiciona latência ao carregamento do app       | Baixa         | Cálculo é leve (queries simples). Se > 500ms, considerar cache de 5 minutos |
| 5  | Badge na navegação pode ser intrusivo para quem não quer alertas | Baixa       | Badge desaparece quando alertas são vistos. Configurações permitem desabilitar tipos que incomodam |

---

## 16. Fora de escopo (futuro)

| Item | Motivo |
|------|--------|
| Notificação por email | Requer coleta de email, serviço de envio, templates. CR separada |
| Notificação push (mobile) | Requer app nativo ou PWA com service worker. CR separada |
| Integração WhatsApp | Depende de F11 (Copiloto WhatsApp) |
| Alerta por categoria ("Alimentação ultrapassou X") | Depende de sistema de limites por categoria (feature futura) |
| Análise sob demanda (botão no card de alertas) | Planejado para extensão da F06 |
| Histórico de alertas resolvidos | Nice-to-have, não essencial para MVP |

---

## 17. Changelog

| Versão | Data       | Autor           | Descrição           |
|--------|------------|-----------------|---------------------|
| 1.0    | 2026-03-18 | Rafael Peixoto  | Criação do CR-033   |
| 1.1    | 2026-03-18 | Rafael Peixoto  | CR-033 concluído — sistema de alertas inteligentes implementado (8 tipos A1-A8, 3 pontos de exibição, 5 endpoints, 26 testes backend, componentes frontend) |
