# Change Request — CR-017: Remover opção "Duplicar" dos gastos planejados

**Versão:** 1.0
**Data:** 2026-03-12
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

Remover o botão "Duplicar" da tabela de despesas planejadas (ExpenseTable). O endpoint backend permanece disponível mas não será mais acessível pela UI.

---

## 2. Classificação

| Campo            | Valor                          |
|------------------|--------------------------------|
| Tipo             | Mudança de Regra de Negócio    |
| Origem           | Feedback do usuário            |
| Urgência         | Backlog                        |
| Complexidade     | Baixa                          |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
A tabela de despesas planejadas exibe três botões de ação por linha: "Editar", "Duplicar" e "Excluir".

### Problema ou Necessidade
A opção "Duplicar" não é útil e adiciona complexidade visual desnecessária à interface.

### Situação Desejada (TO-BE)
A tabela de despesas planejadas exibe apenas dois botões de ação: "Editar" e "Excluir".

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                     | Antes (AS-IS)                        | Depois (TO-BE)                  |
|----|--------------------------|--------------------------------------|---------------------------------|
| 1  | Botões de ação na tabela | Editar, Duplicar, Excluir            | Editar, Excluir                 |
| 2  | Hook useDuplicateExpense | Importado e utilizado                | Removido (código morto)         |
| 3  | API duplicateExpense     | Exportada e utilizada                | Removida (código morto)         |

### 4.2 O que NÃO muda

- Endpoint backend `POST /api/expenses/{id}/duplicate` permanece disponível
- Funcionalidades de Editar e Excluir
- Layout geral da tabela

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária         |
|-----------------------------------|------------|-----------------|-------------------------|
| `/docs/01-PRD.md`                 | Não        | —               | —                       |
| `/docs/02-ARCHITECTURE.md`        | Não        | —               | —                       |
| `/docs/03-SPEC.md`                | Não        | —               | —                       |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | —               | —                       |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —               | —                       |
| `CLAUDE.md`                       | Sim        | Change Requests | Adicionar CR-017        |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                              | Descrição da Mudança                              |
|-----------|------------------------------------------------|----------------------------------------------------|
| Modificar | `frontend/src/components/ExpenseTable.tsx`      | Remover botão Duplicar, import e handler           |
| Modificar | `frontend/src/hooks/useExpenses.ts`             | Remover hook useDuplicateExpense                   |
| Modificar | `frontend/src/services/api.ts`                  | Remover função duplicateExpense                    |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|----------------------|
| —    | N/A       | Não                  |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                                    | Depende de | Done When                                    |
|---------|-----------------------------------------------------------|------------|----------------------------------------------|
| CR-T-01 | Remover botão Duplicar e código associado do ExpenseTable  | —          | Botão não aparece, sem erros no console       |
| CR-T-02 | Remover useDuplicateExpense do hook                       | CR-T-01    | Hook removido, sem imports órfãos             |
| CR-T-03 | Remover duplicateExpense da API                           | CR-T-01    | Função removida, sem imports órfãos           |
| CR-T-04 | Verificar build TypeScript                                | CR-T-03    | `tsc --noEmit` passa sem erros                |
| CR-T-05 | Atualizar CLAUDE.md                                       | CR-T-04    | CR-017 listado nos Change Requests            |

---

## 8. Critérios de Aceite

- [ ] Botão "Duplicar" não aparece na tabela de despesas planejadas
- [ ] Botões "Editar" e "Excluir" continuam funcionando
- [ ] Build TypeScript passa sem erros
- [ ] Código morto (hook + API) removido
- [ ] CLAUDE.md atualizado

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação       |
|----|--------------------------|---------------|---------|-----------------|
| 1  | Nenhum risco identificado | —            | —       | —               |

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo
- **Método:** `git revert [hash]`
- Mudança puramente frontend, sem risco.

### 10.2 Rollback de Migration
- N/A — sem migration.

### 10.3 Impacto em Dados
- N/A — sem alteração de dados.

### 10.4 Rollback de Variaveis de Ambiente
- N/A — nenhuma variável alterada.

### 10.5 Verificacao Pos-Rollback
- [ ] Aplicação acessível e funcional
- [ ] Botão "Duplicar" restaurado

---

## Changelog

| Data       | Autor  | Descrição           |
|------------|--------|---------------------|
| 2026-03-12 | Rafael | CR criado           |
| 2026-03-12 | Rafael | Implementação concluída |
