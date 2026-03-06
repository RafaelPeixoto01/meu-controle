# Change Request — CR-013: Fix Layout Tabela de Despesas

**Versão:** 1.0
**Data:** 2026-03-06
**Status:** Em Implementação
**Autor:** Rafael
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

Na aba de gastos planejados (MonthlyView), o botão "Excluir" na coluna de ações da tabela de despesas está colado na borda direita do container, dando a impressão de que a borda está faltando. A causa é a combinação de `overflow-hidden` no container externo com a tabela sendo comprimida (`w-full`) sem largura mínima, fazendo o conteúdo da última coluna ser clipado.

---

## 2. Classificação

| Campo            | Valor                    |
|------------------|--------------------------|
| Tipo             | Bug Fix                  |
| Origem           | Feedback do usuário      |
| Urgência         | Próxima sprint           |
| Complexidade     | Baixa                    |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
A tabela de despesas usa `w-full` sem `min-width`, e o container externo tem `overflow-hidden`. Em certas resoluções, a coluna de ações é comprimida e o texto "Excluir" fica cortado na borda direita.

### Problema ou Necessidade
O botão "Excluir" aparece sem margem à direita, aparentando falta de borda no container. Prejudica a usabilidade e a aparência visual.

### Situação Desejada (TO-BE)
A tabela deve ter largura mínima suficiente para exibir todas as colunas sem clipar conteúdo. Em telas menores, o `overflow-x-auto` já existente permite scroll horizontal.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)            | Depois (TO-BE)                     |
|----|-------------------------|--------------------------|------------------------------------|
| 1  | Classe da `<table>`     | `w-full`                 | `w-full min-w-[700px]`            |

### 4.2 O que NÃO muda

- Estrutura de colunas da tabela
- Padding das células
- Layout responsivo (scroll horizontal já funciona via `overflow-x-auto`)
- Footer com totalizadores
- Funcionalidade dos botões de ação

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária          |
|-----------------------------------|------------|-----------------|--------------------------|
| `/docs/01-PRD.md`                 | Não        | —               | —                        |
| `/docs/02-ARCHITECTURE.md`        | Não        | —               | —                        |
| `/docs/03-SPEC.md`                | Não        | —               | —                        |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | —               | —                        |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —               | —                        |
| `CLAUDE.md`                       | Sim        | CRs concluídos  | Adicionar CR-013         |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                              | Descrição da Mudança                      |
|-----------|------------------------------------------------|--------------------------------------------|
| Modificar | `frontend/src/components/ExpenseTable.tsx`      | Adicionar `min-w-[700px]` na tag `<table>` |

### 6.2 Banco de Dados

Nenhum impacto.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                          | Depende de | Done When                                    |
|---------|-------------------------------------------------|------------|----------------------------------------------|
| CR-T-01 | Adicionar `min-w-[700px]` na tabela de despesas | —          | Botão "Excluir" visível com espaço à direita |
| CR-T-02 | Verificar build TypeScript                      | CR-T-01    | `tsc --noEmit` passa sem erros               |
| CR-T-03 | Atualizar CLAUDE.md                             | CR-T-02    | CR-013 listado nos CRs concluídos            |

---

## 8. Critérios de Aceite

- [x] Botão "Excluir" visível por completo, com espaço adequado à borda direita
- [x] Layout desktop mantém aparência normal sem scroll desnecessário
- [x] Em telas pequenas, scroll horizontal funciona corretamente
- [x] Footer (totalizadores) não é afetado
- [x] Build TypeScript passa sem erros

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                          | Probabilidade | Impacto | Mitigação                                  |
|----|---------------------------------------------------|---------------|---------|---------------------------------------------|
| 1  | Scroll horizontal aparece em telas entre 700-750px | Baixa         | Baixo   | Comportamento esperado e aceitável          |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código

- **Método:** `git revert [hash]` → merge em `master` → push
- Mudança é CSS-only, rollback trivial

### 10.2 Rollback de Migration

Não aplicável.

### 10.3 Impacto em Dados

Não aplicável.

### 10.4 Rollback de Variáveis de Ambiente

Nenhuma.

### 10.5 Verificação Pós-Rollback

- [ ] Tabela de despesas renderiza corretamente

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-03-06 | Rafael | CR criado e implementado     |
