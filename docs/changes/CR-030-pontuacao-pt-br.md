# Change Request — CR-030: Corrigir Acentuação PT-BR em Textos do Sistema

**Versão:** 1.0
**Data:** 2026-03-16
**Status:** Em Implementação
**Autor:** Rafael
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

Corrigir acentuação e diacríticos do Português do Brasil em todos os textos do sistema: labels, mensagens de erro, placeholders, títulos (user-facing), e docstrings/comentários do código (interno). Exemplos: "nao" → "não", "Descricao" → "Descrição", "conexao" → "conexão".

---

## 2. Classificação

| Campo            | Valor                              |
|------------------|------------------------------------|
| Tipo             | Bug Fix (qualidade de texto)       |
| Origem           | Feedback do usuário                |
| Urgência         | Backlog                            |
| Complexidade     | Baixa                              |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
Diversos textos no frontend (labels, mensagens de erro, placeholders, botões) e no backend (mensagens de erro HTTP, conteúdo de email, docstrings, comentários) estão sem acentuação correta do Português do Brasil.

### Problema ou Necessidade
A falta de acentuação afeta a qualidade percebida pelo usuário e a legibilidade do código. Mensagens como "Verifique sua conexao" e "Sessao expirada" passam uma impressão de descuido.

### Situação Desejada (TO-BE)
Todos os textos visíveis ao usuário e toda documentação interna (docstrings/comentários) devem usar acentuação correta do PT-BR.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                    | Depois (TO-BE)                   |
|----|-------------------------------|----------------------------------|----------------------------------|
| 1  | Labels/títulos frontend       | "Descricao", "Acoes", "Proximo" | "Descrição", "Ações", "Próximo" |
| 2  | Mensagens de erro frontend    | "conexao", "Sessao expirada"    | "conexão", "Sessão expirada"    |
| 3  | Mensagens de erro backend     | "nao encontrada", "invalido"    | "não encontrada", "inválido"    |
| 4  | Conteúdo de email             | "Recuperacao de Senha", "Ola"   | "Recuperação de Senha", "Olá"   |
| 5  | Docstrings/comentários Python | "criacao", "atualizacao", "mes" | "criação", "atualização", "mês" |

### 4.2 O que NÃO muda

- Nomes de variáveis, funções, campos, colunas do banco (ex: `descricao`, `mes_referencia`)
- Nomes de props, tipos TypeScript, campos de API response
- Nenhuma lógica de negócio
- Nenhum endpoint, schema ou migration

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas           | Ação Necessária            |
|-----------------------------------|------------|---------------------------|----------------------------|
| `/docs/01-PRD.md`                 | Não        | —                         | —                          |
| `/docs/02-ARCHITECTURE.md`        | Não        | —                         | —                          |
| `/docs/03-SPEC.md`                | Não        | —                         | —                          |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | —                         | —                          |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                         | —                          |
| `CLAUDE.md`                       | Sim        | Change Requests, Última Tarefa | Adicionar CR-030       |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                          | Descrição da Mudança                  |
|-----------|-------------------------------------------------------------|---------------------------------------|
| Modificar | `frontend/src/pages/*.tsx` (9 arquivos)                     | Corrigir strings user-facing          |
| Modificar | `frontend/src/components/*.tsx` (~14 arquivos)              | Corrigir labels e headers de tabela   |
| Modificar | `frontend/src/services/api.ts`                              | Corrigir "Sessao expirada"            |
| Modificar | `frontend/src/contexts/AuthContext.tsx`                      | Corrigir comentário                   |
| Modificar | `backend/app/routers/auth.py`                               | Corrigir mensagens de erro HTTP       |
| Modificar | `backend/app/routers/expenses.py`                           | Corrigir mensagens de erro HTTP       |
| Modificar | `backend/app/routers/incomes.py`                            | Corrigir mensagens de erro HTTP       |
| Modificar | `backend/app/routers/users.py`                              | Corrigir mensagens de erro HTTP       |
| Modificar | `backend/app/email_service.py`                              | Corrigir subject e body do email      |
| Modificar | `backend/app/auth.py`                                       | Corrigir mensagens de erro/startup    |
| Modificar | `backend/app/main.py`                                       | Corrigir mensagens de warning         |
| Modificar | `backend/app/schemas.py`                                    | Corrigir docstrings                   |
| Modificar | `backend/app/crud.py`                                       | Corrigir docstrings                   |
| Modificar | `backend/app/services.py`                                   | Corrigir docstrings e comentários     |
| Modificar | `backend/app/health_score.py`                               | Corrigir docstrings                   |
| Modificar | `backend/app/routers/daily_expenses.py`                     | Corrigir docstrings                   |
| Modificar | `backend/app/routers/score.py`                              | Corrigir docstrings                   |
| Modificar | `backend/app/routers/months.py`                             | Corrigir comentário                   |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|----------------------|
| N/A  | Nenhuma mudança no banco | Não |

---

## 7. Tarefas de Implementação

| ID        | Tarefa                                                    | Depende de | Done When                                    |
|-----------|-----------------------------------------------------------|------------|----------------------------------------------|
| CR-030-T-01 | Corrigir textos user-facing (frontend + backend errors) | —          | Build TS passa, strings corrigidas           |
| CR-030-T-02 | Corrigir docstrings e comentários do backend            | CR-030-T-01 | Import Python funciona, docstrings corrigidas |
| CR-030-T-03 | Verificação regressiva + atualizar docs + merge         | CR-030-T-02 | Grep sem falsos, CLAUDE.md atualizado        |

---

## 8. Critérios de Aceite

- [ ] Todos os textos visíveis ao usuário usam acentuação correta PT-BR
- [ ] Todas as mensagens de erro HTTP usam acentuação correta
- [ ] Conteúdo de email usa acentuação correta
- [ ] Build TypeScript passa sem erros
- [ ] Import Python funciona sem erros de sintaxe
- [ ] Nenhum nome de variável/função/campo foi alterado
- [ ] Documentos afetados foram atualizados (CLAUDE.md)

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                     | Probabilidade | Impacto | Mitigação                           |
|----|----------------------------------------------|---------------|---------|-------------------------------------|
| 1  | Alterar acidentalmente nome de variável      | Baixa         | Médio   | Lista explícita de exclusões no plano |
| 2  | Quebrar string que é usada como chave/lookup | Baixa         | Alto    | Alterar apenas strings literais de display |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- **Método:** `git revert [hash(es)]` — mudança puramente textual, revert trivial
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard

### 10.2 Rollback de Migration
- N/A — nenhuma migration

### 10.3 Impacto em Dados
- N/A — nenhuma alteração em dados

### 10.4 Rollback de Variáveis de Ambiente
- N/A — nenhuma variável nova/alterada

### 10.5 Verificação Pós-Rollback
- N/A — rollback trivial

---

## Changelog

| Data       | Autor  | Descrição          |
|------------|--------|--------------------|
| 2026-03-16 | Rafael | CR criado          |
