# Change Request — CR-048: Migrar os serviços de IA para Claude Opus 5

**Versão:** 1.0
**Data:** 2026-08-12
**Status:** Em Implementação
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Migrar os dois serviços que chamam a API Anthropic — **Análise Financeira por IA** (F06, CR-032) e **Importação de Extratos** (F07, CR-046) — do modelo depreciado `claude-sonnet-4-20250514` para **`claude-opus-5`**, ajustando os parâmetros da chamada que mudaram entre as gerações de modelo.

Não é uma simples troca de string: os modelos atuais **rejeitam com HTTP 400** o parâmetro `temperature` que ambos os serviços passam hoje, e ligam raciocínio (*thinking*) por padrão — o que quebra a leitura da resposta como ela está escrita. Trocar apenas a variável `CLAUDE_MODEL` no Railway derrubaria as duas features.

---

## 2. Classificação

| Campo            | Valor                                    |
|------------------|------------------------------------------|
| Tipo             | Mudança de Arquitetura / Dívida técnica   |
| Origem           | Dívida técnica (modelo depreciado)        |
| Urgência         | Imediata                                  |
| Complexidade     | Média                                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

Ambos os serviços foram escritos contra a geração Claude Sonnet 4 e compartilham o mesmo padrão de chamada:

| Item | `ai_analysis.py` (CR-032) | `import_service.py` (CR-046) |
|------|---------------------------|------------------------------|
| Modelo default | `claude-sonnet-4-20250514` | `claude-sonnet-4-20250514` |
| `temperature` | `0.3` | `0` |
| `max_tokens` | `2048` | `8192` |
| Timeout | `30s` | `90s` |
| Leitura da resposta | `response.content[0].text` | `response.content[0].text` |

### Problema ou Necessidade

Quatro problemas, sendo dois deles bugs latentes que só aparecem depois da troca de modelo:

1. **Modelo depreciado.** `claude-sonnet-4-20250514` está marcado como *deprecated* pela Anthropic, com retirada anunciada para meados de 2026. Quando um modelo é retirado a API responde 404 e as duas features passam a exibir a mensagem de indisponibilidade em vez de funcionar — de forma silenciosa, porque ambas degradam graciosamente por design.

2. **`temperature` é rejeitado.** Os modelos atuais (Opus 5, Opus 4.7+, Sonnet 5) removeram os parâmetros de amostragem; enviá-los retorna **400**. É o que impede resolver o item 1 apenas mudando a variável de ambiente.

3. **`response.content[0].text` quebra com thinking ligado (bug latente).** Com raciocínio ativo — o padrão no Opus 5 — o primeiro bloco da resposta é um bloco `thinking`, não `text`. O acesso posicional levantaria `AttributeError` a cada chamada, seria engolido pelo `except Exception` do retry, e as duas features falhariam após 3 tentativas sem indicar a causa real.

4. **`max_tokens=2048` na análise trunca com thinking (bug latente).** `max_tokens` limita raciocínio **e** resposta somados. Com thinking ligado, 2048 tokens não comportam o JSON de 8 seções da análise financeira.

### Situação Desejada (TO-BE)

Os dois serviços rodando em `claude-opus-5`, com os parâmetros ajustados à geração atual e a leitura da resposta robusta a blocos de raciocínio. Configuração de thinking sob medida por serviço, conforme o perfil de cada carga de trabalho.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|---------------|----------------|
| 1  | Modelo default (`CLAUDE_MODEL`) | `claude-sonnet-4-20250514` | `claude-opus-5` |
| 2  | `temperature` | `0.3` (análise) / `0` (importação) | Removido de ambos |
| 3  | Thinking | Inexistente na geração anterior | Adaptativo em ambos; importação com `effort: low` |
| 4  | `max_tokens` | 2048 (análise) / 8192 (importação) | 8192 (análise) / 16000 (importação) |
| 5  | Timeout default | 30s (análise) / 90s (importação) | 120s (análise) / 180s (importação) |
| 6  | Leitura da resposta | `content[0].text` (posicional) | Busca o primeiro bloco `type == "text"` |
| 7  | Recusa da IA | Cai no retry genérico (3 chamadas gastas) | `stop_reason == "refusal"` tratado sem retry |

### 4.2 Por que thinking ligado também na importação

A decisão inicial era desligar o raciocínio na importação (tarefa mecânica, mais barata). Ao implementar, a documentação da API mostrou que **desligar thinking no Opus 5 tem um efeito colateral conhecido**: o modelo ocasionalmente vaza tags XML internas (`<thinking>`) no texto visível da resposta. Como a importação faz *parse* de JSON da resposta, um vazamento quebraria o `_parse_ai_json` e desperdiçaria uma chamada cara (o PDF é reenviado a cada retry).

A recomendação oficial para reduzir custo é **manter o raciocínio ligado e baixar o `effort`**, e não desligá-lo. É o que este CR faz: `effort: "low"` na importação (extração é mecânica) e `effort` padrão na análise (tarefa de julgamento, roda 1x/mês com cache).

### 4.3 O que NÃO muda

- Contratos de API — nenhum endpoint, request ou response muda de forma
- Lógica de negócio: dedup por fingerprint, staging, conciliação, cache mensal da análise
- Estrutura de prompts (`backend/prompts/*.txt`) — inalterada
- Schema do banco — sem migration
- Frontend — apenas um texto de aviso de tempo na tela de upload

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Não | — | Migração de modelo não altera funcionalidade, RF, US ou regra de negócio. A dependência "API Anthropic (Claude)" já está registrada e não cita modelo. **PRD não requer atualização — troca de infraestrutura sem nova funcionalidade.** |
| `/docs/02-ARCHITECTURE.md` | Sim | ADRs | Novo ADR-019 (escolha do modelo e restrições da geração atual) |
| `/docs/specs/09-analise-ia.md` | Sim | Variáveis de ambiente, arquitetura | Novos defaults de modelo, timeout e max_tokens |
| `/docs/specs/10-importacao-extratos.md` | Sim | Variáveis de ambiente, arquitetura | Idem + `effort` |
| `/docs/03-SPEC.md` | Não | — | Índice não cita modelos |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Visão geral | Registrar CR-048 |
| `/docs/05-DEPLOY-GUIDE.md` | Sim | Variáveis de ambiente (dev e produção) | Novos defaults |
| `backend/.env.example` | Sim | Blocos de IA e importação | Novos defaults |
| `CLAUDE.md` | Sim | Change Requests, variáveis de ambiente | Adicionar CR-048 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho do Arquivo | Descrição da Mudança |
|------|--------------------|-----------------------|
| Modificar | `backend/app/ai_analysis.py` | `call_anthropic_api`: default do modelo, remover `temperature`, thinking adaptativo, `max_tokens` 8192, timeout 120s, extração do bloco de texto, tratar recusa |
| Modificar | `backend/app/import_service.py` | `call_import_api`: idem + `effort: low`, `max_tokens` 16000, timeout 180s |
| Modificar | `backend/tests/test_ai_analysis.py` | Mocks com blocos tipados; novos testes de parâmetros e recusa |
| Modificar | `backend/tests/test_imports.py` | Idem para o serviço de importação |
| Modificar | `frontend/src/components/imports/ImportUpload.tsx` | Aviso de tempo de processamento (até ~3 min) |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| — | Nenhuma alteração de schema | Não |

### 6.3 Variáveis de Ambiente

| Variável | Default antes | Default depois | Observação |
|----------|---------------|----------------|------------|
| `CLAUDE_MODEL` | `claude-sonnet-4-20250514` | `claude-opus-5` | Deve ser um modelo da geração 4.6+; modelos anteriores não aceitam thinking adaptativo |
| `AI_ANALYSIS_TIMEOUT_SECONDS` | `30` | `120` | Raciocínio aumenta o tempo da chamada |
| `IMPORT_TIMEOUT_SECONDS` | `90` | `180` | Idem, sobre um PDF de várias páginas |

---

## 7. Tarefas de Implementação

| ID | Tarefa | Depende de | Done When |
|----|--------|------------|-----------|
| CR-T-01 | Migrar `call_anthropic_api` (análise) | — | Sem `temperature`; thinking adaptativo; testes passam |
| CR-T-02 | Migrar `call_import_api` (importação) | — | Idem + `effort: low` |
| CR-T-03 | Extração robusta do bloco de texto + tratamento de recusa nos dois serviços | CR-T-01, CR-T-02 | Resposta iniciada por bloco `thinking` é lida corretamente |
| CR-T-04 | Testes de regressão e novos casos | CR-T-03 | Suíte completa verde |
| CR-T-05 | Ajustar aviso de tempo no frontend | CR-T-02 | tsc + lint + Vitest verdes |
| CR-T-06 | Revisão de segurança e validação runtime | CR-T-04 | Registrado neste CR |
| CR-T-07 | Code review pré-merge (complexidade Média) | CR-T-06 | Findings tratados |
| CR-T-08 | Atualizar documentação | CR-T-07 | Docs sincronizados |

---

## 8. Critérios de Aceite

- [ ] Nenhuma chamada à API envia `temperature` (verificado nos kwargs do mock)
- [ ] Default de `CLAUDE_MODEL` é `claude-opus-5` nos dois serviços
- [ ] Resposta cujo primeiro bloco é `thinking` é lida corretamente (texto extraído do bloco certo)
- [ ] Resposta com `stop_reason == "refusal"` falha imediatamente com mensagem clara, sem consumir os retries
- [ ] `max_tokens` e timeouts ajustados conforme a seção 6.3
- [ ] Importação envia `effort: low`; análise usa o padrão
- [ ] Testes existentes continuam passando (regressão backend + frontend)
- [ ] Novos testes cobrem a mudança
- [ ] Fluxo afetado exercitado em runtime antes do merge — ou "N/A" com justificativa
- [ ] Revisão de código pré-merge executada (complexidade Média)
- [ ] Revisão de segurança executada ou justificada
- [ ] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** Status só vai para "Concluído" com todos os critérios `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Custo por importação sobe (Opus custa ~1,7x o Sonnet, e thinking gera tokens extras) | Alta (esperado) | Baixo | Decisão consciente do usuário por qualidade de conciliação; `effort: low` limita o raciocínio; volume é de poucas faturas/mês. Consumo real fica registrado em `import_batches.tokens_input/output` |
| 2 | Chamada mais lenta pode estourar o timeout em fatura grande | Média | Médio | Timeouts elevados (120s/180s) e aviso de tempo ajustado na UI; erro já degrada graciosamente sem 5xx |
| 3 | `max_tokens` insuficiente trunca o JSON em fatura muito grande | Baixa | Médio | 16000 tokens na importação (2x o anterior); `_parse_ai_json` repara JSON truncado; tela de revisão expõe o resultado antes de gravar |
| 4 | `CLAUDE_MODEL` setado no Railway para um modelo antigo continua quebrado | Média | Alto | Documentado no Deploy Guide e no CLAUDE.md que a variável exige modelo 4.6+; **conferir o valor no Railway antes do deploy** |
| 5 | Opus 5 tem salvaguardas de segurança que podem recusar conteúdo | Baixa | Baixo | Recusa tratada explicitamente com mensagem clara; extrato bancário é conteúdo benigno |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-048` → `git revert [hash(es)]` → merge em `master` → push
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** commits da branch `feat/CR-048-migracao-modelo-ia`

### 10.2 Rollback de Migration

- N/A — sem migration.

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** Não. Análises e lotes de importação já gravados permanecem; apenas o modelo usado nas próximas chamadas muda.

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** nenhuma variável nova — apenas defaults no código (`CLAUDE_MODEL`, `AI_ANALYSIS_TIMEOUT_SECONDS`, `IMPORT_TIMEOUT_SECONDS`).
- **Acao de rollback:** o reverso do código restaura os defaults anteriores. Atenção: se o rollback voltar o default para o Sonnet 4 depreciado, as features podem ficar indisponíveis por retirada do modelo — nesse caso preferir setar `CLAUDE_MODEL` no Railway para um modelo atual em vez de reverter.

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] `GET /api/analysis` responde sem 5xx
- [ ] `POST /api/imports` responde sem 5xx
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-08-12 | Claude | CR criado. Modelo escolhido pelo usuário (Opus 5 nos dois serviços); thinking sob medida por serviço. Registrados dois bugs latentes descobertos na análise (`content[0].text` e `max_tokens=2048`) |
