# Change Request — CR-016: Categorização de Despesas Planejadas (F01)

**Versão:** 1.0
**Data:** 2026-03-12
**Status:** Concluído
**Autor:** Claude
**Prioridade:** Crítica

---

## 1. Resumo da Mudança

Adicionar campos `categoria` e `subcategoria` ao modelo de despesas planejadas (`Expense`), reutilizando a árvore de categorias já existente para gastos diários. Permite classificar despesas como "Moradia > Aluguel", "Transporte > Combustível", etc. Esta é a funcionalidade F01 do roadmap, identificada como P0-Crítica e pré-requisito para dashboard (F02), análise por IA (F06) e relatórios (F09).

---

## 2. Classificação

| Campo            | Valor                                      |
|------------------|--------------------------------------------|
| Tipo             | Nova Feature                               |
| Origem           | Evolução do produto (Roadmap F01)          |
| Urgência         | Próxima sprint                             |
| Complexidade     | Média                                      |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
- Despesas planejadas (`Expense`) possuem apenas: nome, valor, vencimento, parcelas, recorrente, status
- Não há nenhum campo de categoria — impossível analisar composição de gastos
- Gastos diários (`DailyExpense`) já possuem `categoria` e `subcategoria` com 14 categorias definidas em `categories.py`
- 100% dos concorrentes oferecem categorização de despesas (benchmark)

### Problema ou Necessidade
- Sem categorização, o MeuControle permanece uma "planilha digital" — não é possível responder "quanto gasto em moradia?" ou "qual % vai para lazer?"
- Categorização é pré-requisito para F02 (dashboard), F04 (score saúde financeira), F06 (IA) e F09 (relatórios)

### Situação Desejada (TO-BE)
- Despesas planejadas têm campos opcionais `categoria` e `subcategoria`
- Usuário seleciona categoria/subcategoria ao criar ou editar despesa (via selects cascading)
- Backend deriva `categoria` automaticamente a partir de `subcategoria`
- Tabela de despesas exibe a subcategoria em cada linha
- Categorias propagam para parcelas futuras e replicações de mês

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                    | Depois (TO-BE)                               |
|----|-------------------------------|----------------------------------|----------------------------------------------|
| 1  | Modelo Expense                | Sem campos de categoria          | + `categoria` (nullable) + `subcategoria` (nullable) |
| 2  | Constante categorias          | `DAILY_EXPENSE_CATEGORIES`       | Renomeada para `EXPENSE_CATEGORIES` (compartilhada) |
| 3  | API expenses                  | Sem endpoint de categorias       | + `GET /api/expenses/categories`             |
| 4  | Criação de despesa            | Sem categoria                    | Aceita `subcategoria` opcional, deriva `categoria` |
| 5  | Criação de parcelas           | Sem propagação de categoria      | Categoria propagada para todas as parcelas futuras |
| 6  | Replicação de mês             | Sem propagação de categoria      | Categoria copiada na replicação              |
| 7  | Duplicação de despesa         | Sem cópia de categoria           | Categoria copiada do original                |
| 8  | Form de despesa (frontend)    | 5 campos                         | + 2 selects cascading (categoria → subcategoria) |
| 9  | Tabela de despesas (frontend) | 7 colunas                        | + coluna "Categoria" (entre Nome e Valor)    |

### 4.2 O que NÃO muda

- Categorias dos gastos diários (`DailyExpense`) — continuam funcionando igual
- Categorias são obrigatórias em gastos diários, opcionais em despesas planejadas
- Métodos de pagamento (`PAYMENT_METHODS`) — sem alteração
- Despesas existentes sem categoria continuam funcionando normalmente (campos nullable)
- Lógica de status (Pendente/Pago/Atrasado) — sem alteração
- Lógica de parcelas e recorrência — sem alteração

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas                | Ação Necessária                    |
|-----------------------------------|------------|--------------------------------|------------------------------------|
| `/docs/01-PRD.md`                 | Não        | —                              | —                                  |
| `/docs/02-ARCHITECTURE.md`        | Sim        | Modelagem de Dados, categories | Atualizar modelo Expense           |
| `/docs/03-SPEC.md`                | Sim        | Schemas, Endpoints expenses    | Add campos e endpoint /categories  |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim        | Header / Tabela de CRs         | Adicionar referência CR-016        |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                              | —                                  |
| `/docs/meucontrole-roadmap-funcionalidades.md` | Sim | F01 | Marcar como concluída |
| `CLAUDE.md`                       | Sim        | Change Requests                | Adicionar CR-016                   |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                  | Descrição da Mudança                              |
|-----------|-----------------------------------------------------|----------------------------------------------------|
| Criar     | `backend/alembic/versions/005_add_expense_categories.py` | Migration: add categoria + subcategoria       |
| Modificar | `backend/app/categories.py`                         | Renomear DAILY_EXPENSE_CATEGORIES → EXPENSE_CATEGORIES |
| Modificar | `backend/app/models.py`                             | Add categoria, subcategoria ao Expense             |
| Modificar | `backend/app/schemas.py`                            | Add campos nos schemas                             |
| Modificar | `backend/app/routers/expenses.py`                   | Add GET /categories, validação, propagação         |
| Modificar | `backend/app/routers/daily_expenses.py`             | Fix import após rename                             |
| Modificar | `backend/app/services.py`                           | Propagar categoria na replicação de mês            |
| Modificar | `frontend/src/types.ts`                             | Add campos nos tipos                               |
| Modificar | `frontend/src/services/api.ts`                      | Add fetchExpenseCategories()                       |
| Modificar | `frontend/src/hooks/useExpenses.ts`                 | Add useExpenseCategories() hook                    |
| Modificar | `frontend/src/components/ExpenseFormModal.tsx`       | Add selects cascading                              |
| Modificar | `frontend/src/components/ExpenseTable.tsx`           | Add coluna Categoria                               |

### 6.2 Banco de Dados

| Ação      | Descrição                                        | Migration Necessária? |
|-----------|--------------------------------------------------|-----------------------|
| Adicionar | Colunas `categoria` e `subcategoria` em expenses | Sim                   |

**Migration:**
```sql
ALTER TABLE expenses ADD COLUMN categoria VARCHAR(50);
ALTER TABLE expenses ADD COLUMN subcategoria VARCHAR(50);
```

---

## 7. Tarefas de Implementação

| ID       | Tarefa                                                          | Depende de | Done When                                          |
|----------|-----------------------------------------------------------------|------------|-----------------------------------------------------|
| CR-T-01  | Migration 005: add categoria + subcategoria                     | —          | alembic upgrade head + downgrade -1 funciona        |
| CR-T-02  | Renomear DAILY_EXPENSE_CATEGORIES → EXPENSE_CATEGORIES          | —          | Import atualizado em daily_expenses.py              |
| CR-T-03  | Atualizar modelo Expense com novos campos                       | CR-T-01    | Campos mapeados no ORM                              |
| CR-T-04  | Atualizar schemas (Create, Update, Response)                    | CR-T-03    | Schemas aceitam/retornam categoria/subcategoria     |
| CR-T-05  | Add GET /categories + validação em create/update/duplicate      | CR-T-02,04 | Endpoint retorna categorias, validação funciona     |
| CR-T-06  | Propagar categoria na transição de mês                          | CR-T-03    | Despesas replicadas mantêm categoria                |
| CR-T-07  | Atualizar types.ts, api.ts, useExpenses.ts                      | CR-T-05    | Frontend compila sem erros                          |
| CR-T-08  | Add selects cascading no ExpenseFormModal                       | CR-T-07    | Criar/editar despesa com categoria funciona         |
| CR-T-09  | Add coluna Categoria no ExpenseTable                            | CR-T-07    | Tabela mostra subcategoria ou "—"                   |
| CR-T-10  | Build TypeScript + regressão                                    | CR-T-08,09 | tsc --noEmit passa, app funciona                    |
| CR-T-11  | Atualizar documentação (CR, roadmap, ARCH, SPEC, PLAN, CLAUDE)  | CR-T-10    | Docs refletem as mudanças                           |

---

## 8. Critérios de Aceite

- [ ] Despesa pode ser criada com ou sem categoria (campo opcional)
- [ ] Selects cascading funcionam: categoria → subcategoria
- [ ] Backend valida subcategoria contra lista de categorias válidas
- [ ] Backend deriva categoria automaticamente a partir de subcategoria
- [ ] Ao criar despesa parcelada com categoria, todas as parcelas recebem a mesma categoria
- [ ] Ao replicar mês, despesas mantêm categoria
- [ ] Ao duplicar despesa, categoria é copiada
- [ ] Tabela de despesas mostra coluna "Categoria" com subcategoria ou "—"
- [ ] Despesas existentes sem categoria continuam funcionando normalmente
- [ ] GET /api/expenses/categories retorna árvore de categorias
- [ ] Testes existentes continuam passando (regressão)
- [ ] Build TypeScript passa sem erros

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                  | Probabilidade | Impacto | Mitigação                                |
|----|-------------------------------------------|---------------|---------|------------------------------------------|
| 1  | Rename da constante quebra daily_expenses | Baixa         | Alto    | Atualizar import imediatamente após rename |
| 2  | Tabela fica larga demais com nova coluna  | Média         | Baixo   | Subcategoria exibida de forma compacta   |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- **Método:** `git revert [hash]` → merge em `master` → push

### 10.2 Rollback de Migration
- **Migration afetada:** `005_add_expense_categories.py`
- **Comando de downgrade:** `alembic downgrade 004`
- **Downgrade testado?** [ ] Sim
- **Downgrade é destrutivo?** [x] Sim (dados de categoria serão perdidos)

### 10.3 Impacto em Dados
- **Dados serão perdidos no rollback?** [x] Sim — valores de categoria/subcategoria
- **Backup necessário antes do deploy?** [ ] Não (campos novos, sem dados pre-existentes)

### 10.4 Rollback de Variáveis de Ambiente
- **Variáveis novas/alteradas:** Nenhuma

### 10.5 Verificação Pós-Rollback
- [ ] Aplicação acessível e funcional
- [ ] `alembic current` mostra revisão 004
- [ ] Tabela de despesas funciona sem coluna de categoria

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-03-12 | Claude | CR criado                    |
