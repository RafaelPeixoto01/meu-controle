# Change Request — CR-019: Dashboard Visual com Gráficos (F02)

**Versão:** 1.0
**Data:** 2026-03-13
**Status:** Em Implementação
**Autor:** Rafael
**Prioridade:** Crítica

---

## 1. Resumo da Mudança

Implementar dashboard visual com gráficos para o MeuControle, transformando a experiência de planilha digital em uma visão rápida da saúde financeira. O dashboard incluirá: cards de indicadores-chave (saldo livre, % comprometimento, parcelas futuras, gastos diários), donut charts separados para composição por categoria (planejadas e diárias), bar chart de evolução mensal (6 meses), e breakdown de status. Feature F02 do roadmap — P0 Crítica, dependência F01 (categorização) já concluída.

---

## 2. Classificação

| Campo            | Valor                                    |
|------------------|------------------------------------------|
| Tipo             | Nova Feature                             |
| Origem           | Evolução do produto (roadmap F02)        |
| Urgência         | Próxima sprint                           |
| Complexidade     | Alta                                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O MeuControle é uma visão tabular (tipo planilha): tabela de despesas, tabela de receitas, totalizadores numéricos. Não há gráficos, visualizações ou snapshot rápido da saúde financeira. O benchmark mostra que 100% dos concorrentes oferecem dashboards visuais.

### Problema ou Necessidade
Sem visualização gráfica, o usuário precisa analisar linhas de tabela para entender composição de gastos, tendências e comprometimento. Isso é lento, pouco intuitivo e não escala com volume de dados.

### Situação Desejada (TO-BE)
Dashboard como primeira tab no ViewSelector com: 4 KPI cards, 2 donut charts (planejadas e diárias separados), bar chart de evolução 6 meses (3 séries), e breakdown de status. Dados vindos de endpoint dedicado com agregação server-side.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                      | Antes (AS-IS)                    | Depois (TO-BE)                                  |
|----|---------------------------|----------------------------------|------------------------------------------------|
| 1  | Visualização de dados     | Apenas tabelas                   | Dashboard com gráficos + tabelas existentes     |
| 2  | ViewSelector              | 3 tabs (Planejados/Diários/Parcelas) | 4 tabs (Dashboard/Planejados/Diários/Parcelas) |
| 3  | Agregação por categoria   | Não existe                       | Endpoint retorna breakdown por categoria        |
| 4  | Evolução mensal           | Não existe                       | Comparação últimos 6 meses                     |
| 5  | Dependência frontend      | Sem charting library             | recharts adicionado                            |

### 4.2 O que NÃO muda

- Tabelas de despesas/receitas (MonthlyView)
- Tabela de gastos diários (DailyExpensesView)
- Visão de parcelas (InstallmentsView)
- Modelos de dados (sem migrations)
- Endpoints existentes
- Lógica de auto-generate e status detection

---

## 5. Impacto nos Documentos

| Documento                          | Impactado? | Seções Afetadas                   | Ação Necessária           |
|------------------------------------|------------|-----------------------------------|---------------------------|
| `/docs/01-PRD.md`                  | Não        | —                                 | —                         |
| `/docs/02-ARCHITECTURE.md`        | Sim        | Stack tecnológica, Estrutura      | Adicionar recharts, router |
| `/docs/03-SPEC.md`                | Sim        | Features, Endpoints               | Adicionar spec dashboard   |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim        | Visão geral, Tarefas              | Adicionar CR-019 tasks     |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                                 | —                         |
| `CLAUDE.md`                       | Sim        | Estrutura, CRs, última tarefa     | Atualizar                 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                      | Descrição da Mudança                    |
|-----------|---------------------------------------------------------|-----------------------------------------|
| Criar     | `backend/app/routers/dashboard.py`                      | Endpoint GET /api/dashboard/{year}/{month} |
| Modificar | `backend/app/schemas.py`                                | +3 schemas dashboard                    |
| Modificar | `backend/app/services.py`                               | +get_dashboard_data()                   |
| Modificar | `backend/app/crud.py`                                   | +3 funções de query agregada            |
| Modificar | `backend/app/main.py`                                   | Registrar dashboard router              |
| Criar     | `frontend/src/hooks/useDashboard.ts`                    | Hook TanStack Query                     |
| Criar     | `frontend/src/components/dashboard/CategoryDonutChart.tsx` | Donut chart reutilizável             |
| Criar     | `frontend/src/components/dashboard/EvolutionBarChart.tsx`  | Bar chart 3 séries                   |
| Criar     | `frontend/src/components/dashboard/KeyIndicators.tsx`      | Grid de KPI cards                    |
| Criar     | `frontend/src/components/dashboard/StatusBreakdown.tsx`    | Barra horizontal de status           |
| Criar     | `frontend/src/pages/DashboardView.tsx`                     | Página dashboard                     |
| Modificar | `frontend/src/types.ts`                                    | +3 interfaces                        |
| Modificar | `frontend/src/services/api.ts`                             | +fetchDashboard()                    |
| Modificar | `frontend/src/App.tsx`                                     | +rota /dashboard                     |
| Modificar | `frontend/src/components/ViewSelector.tsx`                 | +tab Dashboard (1ª posição)          |

### 6.2 Banco de Dados

| Ação | Descrição           | Migration Necessária? |
|------|---------------------|-----------------------|
| —    | Nenhuma alteração   | Não                   |

---

## 7. Tarefas de Implementação

| ID         | Tarefa                                                    | Depende de | Done When                                        |
|------------|-----------------------------------------------------------|------------|--------------------------------------------------|
| CR-019-T-01 | Backend: schemas, crud, service, router dashboard        | —          | Endpoint retorna DashboardResponse completo       |
| CR-019-T-02 | Backend: testes do endpoint dashboard                    | T-01       | Testes passam cobrindo cenários principais        |
| CR-019-T-03 | Instalar recharts                                        | —          | package.json atualizado, npm install ok           |
| CR-019-T-04 | Frontend: types, API function, hook useDashboard         | T-01       | Hook retorna dados tipados do endpoint            |
| CR-019-T-05 | Frontend: componentes visuais (KPIs, Donuts, Bar, Status) | T-03, T-04 | Componentes renderizam com dados mock             |
| CR-019-T-06 | Frontend: DashboardView page                             | T-05       | Página monta todos os componentes                 |
| CR-019-T-07 | Frontend: rota App.tsx + tab ViewSelector                | T-06       | Navegação funciona, tab ativa                     |
| CR-019-T-08 | Atualizar documentação                                   | T-01~T-07  | Docs refletem todas as mudanças                   |

---

## 8. Critérios de Aceite

- [ ] Dashboard acessível via tab "Dashboard" no ViewSelector (primeira posição)
- [ ] KPI cards mostram: Saldo Livre, % Comprometimento, Parcelas Futuras, Gastos Diários
- [ ] Donut chart de despesas planejadas por categoria renderiza com cores e legendas
- [ ] Donut chart de gastos diários por categoria renderiza separadamente
- [ ] Bar chart mostra evolução de 6 meses com 3 séries (receitas/planejadas/diários)
- [ ] Status breakdown mostra proporção Pago/Pendente/Atrasado
- [ ] MonthNavigator funciona no dashboard (muda mês, recarrega dados)
- [ ] Layout responsivo (desktop: 2 colunas para charts; mobile: empilhado)
- [ ] Testes existentes continuam passando (regressão)
- [ ] Build TypeScript passa sem erros
- [ ] Documentos afetados foram atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                    | Probabilidade | Impacto | Mitigação                                |
|----|---------------------------------------------|---------------|---------|------------------------------------------|
| 1  | Performance das queries de evolução (6 meses) | Baixa       | Médio   | Usar SUM() agregado, não fetch all rows  |
| 2  | Despesas sem categoria (pré-CR-016)         | Média         | Baixo   | Agrupar como "Outros"                    |
| 3  | Bundle size do recharts (~150KB gzip)       | Baixa         | Baixo   | Tree-shaking, importar apenas componentes usados |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- **Método:** `git revert [hash]` → merge em `master` → push
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard

### 10.2 Rollback de Migration
- N/A — Nenhuma migration neste CR

### 10.3 Impacto em Dados
- **Dados serão perdidos no rollback?** Não
- **Backup necessário antes do deploy?** Não

### 10.4 Rollback de Variáveis de Ambiente
- **Variáveis novas/alteradas:** Nenhuma

### 10.5 Verificação Pós-Rollback
- [ ] Aplicação acessível e funcional
- [ ] ViewSelector volta a 3 tabs
- [ ] MonthlyView, DailyExpensesView e InstallmentsView funcionam normalmente

---

## Changelog

| Data       | Autor   | Descrição                    |
|------------|---------|------------------------------|
| 2026-03-13 | Rafael  | CR criado                    |
| 2026-03-13 | Rafael  | Implementação iniciada       |
