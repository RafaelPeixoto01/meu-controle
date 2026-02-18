# Change Request — CR-005: Gastos Diarios (Daily Expenses)

**Versao:** 1.0
**Data:** 2026-02-17
**Status:** Concluido
**Autor:** Rafael
**Prioridade:** Alta

---

## 1. Resumo da Mudanca

Adicionar uma nova funcionalidade independente para registrar gastos nao planejados do dia a dia (mercado, transporte, alimentacao, lazer). Inclui modelo de dados proprio, API REST completa, visao mensal agrupada por dia com totais, e menu de navegacao para alternar entre "Gastos Planejados" (existente) e "Gastos Diarios" (novo).

---

## 2. Classificacao

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Nova Feature              |
| Origem           | Evolucao do produto       |
| Urgencia         | Proxima sprint            |
| Complexidade     | Alta                      |

---

## 3. Contexto e Motivacao

### Situacao Atual (AS-IS)
O app possui apenas "Gastos Planejados" — despesas mensais com vencimento, parcelas, recorrencia e status (Pendente/Pago/Atrasado). Nao ha forma de registrar gastos pontuais do dia a dia.

### Problema ou Necessidade
Gastos cotidianos (supermercado, cafe, uber, farmacia) nao se encaixam no modelo de despesas planejadas. O usuario precisa de uma forma rapida de registrar esses gastos com categorizacao e visualizacao mensal.

### Situacao Desejada (TO-BE)
Nova secao "Gastos Diarios" com:
- Registro rapido: descricao, valor, subcategoria, data (default=hoje), metodo de pagamento
- 14 categorias fixas com subcategorias (baseadas em `categorias_gastos.md`) + "Outros"
- 6 metodos de pagamento: Dinheiro, Cartao de Credito, Cartao de Debito, Pix, Vale Alimentacao, Vale Refeicao
- Visao mensal agrupada por dia com subtotais e total do mes
- Menu de navegacao (ViewSelector) para alternar entre as duas visoes

---

## 4. Detalhamento da Mudanca

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                  | Depois (TO-BE)                           |
|----|-------------------------------|--------------------------------|------------------------------------------|
| 1  | Modulos do app                | Apenas Gastos Planejados       | Gastos Planejados + Gastos Diarios       |
| 2  | Modelo de dados               | Expense, Income                | + DailyExpense                           |
| 3  | API                           | /api/expenses, /api/months     | + /api/daily-expenses/*                  |
| 4  | Navegacao                     | Rota unica /                   | / (planejados) + /daily-expenses         |
| 5  | MonthlyView                   | Sem seletor de visao           | ViewSelector no topo                     |

### 4.2 O que NAO muda

- Funcionalidade de Gastos Planejados (Expense) permanece intacta
- Funcionalidade de Receitas (Income) permanece intacta
- SaldoLivre, auto-status detection, month transition — sem alteracoes
- Autenticacao e multi-usuario — sem alteracoes
- Endpoints existentes — sem alteracoes

---

## 5. Impacto nos Documentos

| Documento                        | Impactado? | Secoes Afetadas                    | Acao Necessaria                    |
|----------------------------------|------------|------------------------------------|------------------------------------|
| `/docs/01-PRD.md`                | Sim        | Requisitos Funcionais              | Adicionar RF-13 (Gastos Diarios)   |
| `/docs/02-ARCHITECTURE.md`      | Sim        | Modelagem de Dados, Estrutura      | Adicionar DailyExpense ao ER       |
| `/docs/03-SPEC.md`              | Sim        | Features                           | Nova secao CR-005                  |
| `/docs/04-IMPLEMENTATION-PLAN.md`| Sim       | Grupos de tarefas                  | Adicionar grupo CR-005             |
| `CLAUDE.md`                      | Sim        | Contexto Atual, Estrutura          | Atualizar CRs e estrutura          |

---

## 6. Impacto no Codigo

### 6.1 Arquivos Afetados

| Acao      | Caminho do Arquivo                                    | Descricao da Mudanca                              |
|-----------|-------------------------------------------------------|----------------------------------------------------|
| Criar     | `backend/app/categories.py`                           | Categorias + metodos pagamento + helpers           |
| Modificar | `backend/app/models.py`                               | +DailyExpense model, +User relationship            |
| Criar     | `backend/alembic/versions/004_add_daily_expenses.py`  | Migration para tabela daily_expenses               |
| Modificar | `backend/app/schemas.py`                              | +6 schemas Pydantic                                |
| Modificar | `backend/app/crud.py`                                 | +5 funcoes CRUD                                    |
| Modificar | `backend/app/services.py`                             | +get_daily_expenses_monthly_summary()              |
| Criar     | `backend/app/routers/daily_expenses.py`               | Router com 5 endpoints                             |
| Modificar | `backend/app/main.py`                                 | Registrar router                                   |
| Modificar | `frontend/src/types.ts`                               | +6 interfaces TypeScript                           |
| Modificar | `frontend/src/services/api.ts`                        | +5 funcoes API                                     |
| Criar     | `frontend/src/hooks/useDailyExpenses.ts`              | Hooks TanStack Query                               |
| Criar     | `frontend/src/hooks/useDailyExpensesView.ts`          | Hook navegacao mensal                              |
| Modificar | `frontend/src/utils/format.ts`                        | +formatDateFull()                                  |
| Criar     | `frontend/src/components/DailyExpenseFormModal.tsx`    | Modal formulario                                   |
| Criar     | `frontend/src/components/DailyExpenseTable.tsx`        | Tabela agrupada por dia                            |
| Criar     | `frontend/src/components/ViewSelector.tsx`             | Seletor de visao                                   |
| Criar     | `frontend/src/pages/DailyExpensesView.tsx`            | Pagina principal                                   |
| Modificar | `frontend/src/App.tsx`                                | +rota /daily-expenses                              |
| Modificar | `frontend/src/pages/MonthlyView.tsx`                  | +ViewSelector no topo                              |

### 6.2 Banco de Dados

| Acao  | Descricao                                     | Migration Necessaria? |
|-------|-----------------------------------------------|-----------------------|
| Criar | Tabela `daily_expenses` com 11 colunas        | Sim                   |
| Criar | Indice composto (user_id, mes_referencia)     | Sim                   |
| Criar | Indice em `data`                              | Sim                   |

---

## 7. Tarefas de Implementacao

| ID       | Tarefa                                                           | Depende de      | Done When                                        |
|----------|------------------------------------------------------------------|-----------------|--------------------------------------------------|
| CR5-T-01 | Criar CR-005                                                     | —               | Documento criado seguindo template               |
| CR5-T-02 | Criar `categories.py`                                            | CR5-T-01        | 14 categorias + Outros + 6 metodos + helpers     |
| CR5-T-03 | Adicionar modelo DailyExpense + User relationship                | CR5-T-02        | Model com colunas, indices e FK corretos          |
| CR5-T-04 | Criar migration 004                                              | CR5-T-03        | alembic upgrade/downgrade funciona                |
| CR5-T-05 | Adicionar schemas Pydantic                                       | CR5-T-03        | 6 schemas criados                                |
| CR5-T-06 | Adicionar funcoes CRUD                                           | CR5-T-03        | 5 funcoes CRUD                                   |
| CR5-T-07 | Adicionar service layer                                          | CR5-T-06        | Agrupamento por dia + subtotais funciona          |
| CR5-T-08 | Criar router + registrar em main.py                              | CR5-T-05/06/07  | 5 endpoints respondem corretamente               |
| CR5-T-09 | Adicionar tipos TypeScript                                       | CR5-T-05        | 6 interfaces adicionadas                         |
| CR5-T-10 | Adicionar funcoes API frontend                                   | CR5-T-09        | 5 funcoes em api.ts                              |
| CR5-T-11 | Criar hooks TanStack Query                                       | CR5-T-10        | 5 hooks exportados                               |
| CR5-T-12 | Criar hook de navegacao mensal                                   | CR5-T-11        | Hook com month state + navigation                |
| CR5-T-13 | Adicionar formatDateFull()                                       | —               | Funcao formata "DD/MM - Dia"                     |
| CR5-T-14 | Criar DailyExpenseFormModal                                      | CR5-T-11/13     | Modal com 5 campos, create/edit                  |
| CR5-T-15 | Criar DailyExpenseTable                                          | CR5-T-11/13/14  | Tabela agrupada por dia com totais               |
| CR5-T-16 | Criar ViewSelector                                               | —               | Pills/tabs alternam entre visoes                 |
| CR5-T-17 | Criar DailyExpensesView page                                     | CR5-T-12/15/16  | Pagina renderiza todos componentes               |
| CR5-T-18 | Adicionar rota /daily-expenses                                   | CR5-T-17        | Rota protegida funciona                          |
| CR5-T-19 | Integrar ViewSelector no MonthlyView                             | CR5-T-16/18     | Navegacao entre visoes funciona                  |
| CR5-T-20 | Verificar build completo                                         | CR5-T-19        | tsc, migration, backend sem erros                |
| CR5-T-21 | Atualizar documentacao                                           | CR5-T-20        | Todos docs atualizados                           |

---

## 8. Criterios de Aceite

- [ ] API GET /api/daily-expenses/categories retorna 14 categorias + Outros e 6 metodos de pagamento
- [ ] API POST cria gasto diario com categoria auto-derivada da subcategoria
- [ ] API GET /{year}/{month} retorna gastos agrupados por dia com subtotais e total do mes
- [ ] API PATCH atualiza campos parcialmente (exclude_unset)
- [ ] API DELETE remove gasto diario por ID
- [ ] Validacao rejeita subcategoria invalida (422)
- [ ] Validacao rejeita metodo de pagamento invalido (422)
- [ ] Isolamento multi-usuario: usuario so ve seus gastos (user_id filter)
- [ ] Frontend: formulario com 5 campos (descricao, valor, data, subcategoria, metodo)
- [ ] Frontend: tabela agrupada por dia com subtotal + total do mes
- [ ] Frontend: ViewSelector alterna entre / e /daily-expenses
- [ ] Migration: alembic upgrade head + alembic downgrade -1 funcionam
- [ ] Build: npx tsc --noEmit -p tsconfig.app.json sem erros
- [ ] Testes existentes continuam passando (regressao)
- [ ] Documentos afetados atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral               | Probabilidade | Impacto | Mitigacao                              |
|----|-----------------------------------------|---------------|---------|----------------------------------------|
| 1  | Migration pode conflitar com dados existentes | Baixa    | Medio   | Nova tabela, nao altera tabelas existentes |
| 2  | MonthlyView pode quebrar com ViewSelector | Baixa      | Alto    | Adicao aditiva, nao altera logica existente |

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo

- **Metodo:** `git revert [hash(es)]` + push para `master`
- **Commits a reverter:** Todos os commits com referencia CR-005

### 10.2 Rollback de Migration

- **Migration afetada:** `004_add_daily_expenses.py`
- **Comando de downgrade:** `alembic downgrade 003`
- **Downgrade testado?** [ ] Sim / [ ] Nao
- **Downgrade e destrutivo?** [x] Sim (dados de gastos diarios perdidos)

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** [x] Sim
- **Detalhamento:** Tabela `daily_expenses` sera removida com todos os dados
- **Backup necessario antes do deploy?** [ ] Nao (feature nova, sem dados legados)

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] `alembic current` mostra revisao 003
- [ ] Gastos Planejados continuam funcionando normalmente
- [ ] Usuarios existentes conseguem fazer login

---

## Changelog

| Data       | Autor   | Descricao                    |
|------------|---------|------------------------------|
| 2026-02-17 | Rafael  | CR criado                    |
