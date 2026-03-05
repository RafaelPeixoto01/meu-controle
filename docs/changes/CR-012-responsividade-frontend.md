# Change Request — CR-012: Melhorias de Responsividade no Frontend

**Versão:** 1.0
**Data:** 2026-03-05
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Média

---

## 1. Resumo da Mudança

Corrigir problemas de usabilidade em telas pequenas (< 640px) no frontend. O app já possui uma base responsiva razoável, mas vários componentes apresentam overflow, padding excessivo ou layouts não adaptados para dispositivos móveis.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Mudança de UI / UX Fix    |
| Origem           | Revisão técnica interna   |
| Urgência         | Próxima sprint            |
| Complexidade     | Baixa                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
- ViewSelector com botões de padding fixo (`px-5`) que transbordam em telas < 400px
- MonthNavigator com texto "← Anterior" / "Proximo →" que compete com o label do mês em telas estreitas
- ExpenseFormModal com grid de parcelas (`grid-cols-2`) que não empilha em mobile
- Todas as tabelas com `px-6` fixo nos cells, desperdiçando espaço no scroll horizontal
- Barra de seleção de despesas com layout que espreme em telas < 360px
- InstallmentsView sem ViewSelector nos estados de loading/erro e com padding uniforme

### Problema ou Necessidade
Experiência degradada em dispositivos móveis, especialmente em telas de 320px-375px.

### Situação Desejada (TO-BE)
- Todos os componentes adaptados para telas de 320px+ com classes Tailwind responsivas
- Padding compacto em mobile, expandido em sm+
- Textos secundários ocultos em mobile quando necessário
- Grids que empilham verticalmente em telas estreitas

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Componente          | Antes (AS-IS)              | Depois (TO-BE)                          |
|----|---------------------|----------------------------|-----------------------------------------|
| 1  | ViewSelector        | `px-5 text-sm` fixo       | `px-3 sm:px-5 text-xs sm:text-sm`       |
| 2  | MonthNavigator      | Texto completo sempre      | Só setas em mobile, texto em sm+        |
| 3  | ExpenseFormModal    | `grid-cols-2` fixo         | `grid-cols-1 sm:grid-cols-2`            |
| 4  | Tabelas (cells)     | `px-6` fixo                | `px-3 sm:px-6`                          |
| 5  | ExpenseTable sel.   | `flex` horizontal fixo     | `flex-col sm:flex-row` com gap           |
| 6  | Tabelas (botões)    | `px-2.5` fixo              | `px-1.5 sm:px-2.5`                      |
| 7  | Tabelas (headers)   | `px-6 py-4` fixo           | `px-3 py-3 sm:px-6 sm:py-4`            |
| 8  | InstallmentsView    | Sem ViewSelector no loading | ViewSelector em loading/erro            |
| 9  | InstallmentsView    | `p-6` uniforme             | `px-4 py-6 sm:p-6`                     |

### 4.2 O que NÃO muda

- Lógica de negócio (zero alterações em JS/TS)
- Endpoints e API
- Estrutura de componentes
- Design visual em desktop (apenas CSS responsivo)

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Ação Necessária                |
|-----------------------------------|------------|--------------------------------|
| `/docs/01-PRD.md`                 | Não        | —                              |
| `/docs/02-ARCHITECTURE.md`        | Não        | —                              |
| `/docs/03-SPEC.md`                | Não        | —                              |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | —                              |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                              |
| `CLAUDE.md`                       | Sim        | Adicionar CR-012 na lista      |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                    | Descrição da Mudança              |
|-----------|-------------------------------------------------------|-----------------------------------|
| Modificar | `frontend/src/components/ViewSelector.tsx`             | Padding e font-size responsivos   |
| Modificar | `frontend/src/components/MonthNavigator.tsx`           | Texto oculto em mobile            |
| Modificar | `frontend/src/components/ExpenseFormModal.tsx`         | Grid empilhável                   |
| Modificar | `frontend/src/components/ExpenseTable.tsx`             | Padding, seleção, header, botões  |
| Modificar | `frontend/src/components/IncomeTable.tsx`              | Padding, header, botões           |
| Modificar | `frontend/src/components/DailyExpenseTable.tsx`        | Padding, header, botões           |
| Modificar | `frontend/src/pages/InstallmentsView.tsx`              | ViewSelector + padding mobile     |

### 6.2 Banco de Dados

Nenhuma alteração.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                           | Depende de | Done When                                     |
|---------|--------------------------------------------------|------------|-----------------------------------------------|
| CR-T-01 | ViewSelector: padding/font responsivos           | —          | Sem overflow em 320px                          |
| CR-T-02 | MonthNavigator: texto oculto em mobile           | —          | Setas visíveis, texto só em sm+                |
| CR-T-03 | ExpenseFormModal: grid empilhável                | —          | Parcelas empilham em < 640px                   |
| CR-T-04 | Tabelas: padding responsivo em cells e headers   | —          | Padding compacto em mobile, expandido em sm+   |
| CR-T-05 | ExpenseTable: seleção empilhável + botões        | CR-T-04    | Barra de seleção legível em 320px              |
| CR-T-06 | InstallmentsView: ViewSelector + padding         | —          | ViewSelector em loading/erro, padding mobile   |
| CR-T-07 | Build TypeScript sem erros                       | CR-T-01~06 | `tsc --noEmit` passa                           |

---

## 8. Critérios de Aceite

- [x] Todos os componentes renderizam corretamente em 320px
- [x] ViewSelector não transborda em telas pequenas
- [x] Tabelas fazem scroll horizontal suave em mobile
- [x] Modais não cortam conteúdo em telas pequenas
- [x] Build TypeScript passa sem erros
- [x] Nenhuma alteração de lógica de negócio

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco                             | Probabilidade | Impacto | Mitigação                      |
|----|-----------------------------------|---------------|---------|--------------------------------|
| 1  | Layout desktop alterado           | Baixa         | Baixo   | Classes sm+ preservam desktop  |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código

- **Método:** `git revert [hash]` — alterações são apenas CSS classes
- **Impacto:** Nenhum dado ou estado afetado

### 10.2~10.5

Não aplicável — sem migrations, variáveis de ambiente ou dados afetados.

---

## Changelog

| Data       | Autor  | Descrição           |
|------------|--------|---------------------|
| 2026-03-05 | Rafael | CR criado           |
| 2026-03-05 | Rafael | Implementação concluída |
| 2026-03-05 | Rafael | Validação realizada — status: Concluído |
