# Change Request — CR-020: Trocar card "Parcelas Futuras" por "Gastos Planejados" no Dashboard

**Versão:** 1.0
**Data:** 2026-03-13
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

Substituir o KPI card "Parcelas Futuras" no Dashboard por um card "Gastos Planejados" que exibe o total de despesas planejadas do mês selecionado. O backend já retorna `total_despesas_planejadas` no `DashboardResponse`, portanto a mudança é 100% frontend.

---

## 2. Classificação

| Campo            | Valor                        |
|------------------|------------------------------|
| Tipo             | Mudança de Regra de Negócio  |
| Origem           | Feedback do usuário          |
| Urgência         | Próxima sprint               |
| Complexidade     | Baixa                        |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O terceiro KPI card no Dashboard exibe "Parcelas Futuras" — o valor restante de todas as parcelas ativas (em andamento) do usuário, calculado via `crud.get_installment_expenses_grouped()`.

### Problema ou Necessidade
O usuário prefere ver o total de gastos planejados do mês no card superior, informação mais relevante para a visão mensal do Dashboard.

### Situação Desejada (TO-BE)
O terceiro KPI card exibe "Gastos Planejados" — o total de despesas planejadas do mês selecionado (`total_despesas_planejadas`), valor que já é retornado pelo backend.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                  | Antes (AS-IS)                          | Depois (TO-BE)                           |
|----|-----------------------|----------------------------------------|------------------------------------------|
| 1  | Label do card         | "Parcelas Futuras"                     | "Gastos Planejados"                      |
| 2  | Valor exibido         | `total_parcelas_futuras`               | `total_despesas_planejadas`              |
| 3  | Ícone do card         | `CreditCard` (lucide-react)            | `ClipboardList` (lucide-react)           |
| 4  | Prop do componente    | `totalParcelasFuturas: number`         | `totalDespesasPlanejadas: number`        |

### 4.2 O que NÃO muda

- Backend: endpoint `/api/dashboard/{year}/{month}` inalterado
- Backend: `total_parcelas_futuras` continua sendo calculado e retornado (pode ser útil futuramente)
- Os outros 3 KPI cards (Receitas, Comprometimento, Saldo Livre)
- Gráficos donut, bar chart e status breakdown
- Cor do card (mantém `accent`/azul)

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas             | Ação Necessária              |
|-----------------------------------|------------|-----------------------------|------------------------------|
| `/docs/01-PRD.md`                 | Não        | —                           | —                            |
| `/docs/02-ARCHITECTURE.md`        | Não        | —                           | —                            |
| `/docs/03-SPEC.md`                | Sim        | Dashboard / KPI cards       | Atualizar descrição do card  |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim        | Visão geral de CRs          | Adicionar CR-020             |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                           | —                            |
| `CLAUDE.md`                       | Sim        | Change Requests             | Adicionar CR-020             |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                        | Descrição da Mudança                        |
|-----------|-----------------------------------------------------------|---------------------------------------------|
| Modificar | `frontend/src/components/dashboard/KeyIndicators.tsx`     | Trocar icon, prop, label e valor do card     |
| Modificar | `frontend/src/pages/DashboardView.tsx`                    | Trocar prop passada ao KeyIndicators         |

### 6.2 Banco de Dados

N/A — sem alterações no banco de dados.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                              | Depende de | Done When                                      |
|---------|-----------------------------------------------------|------------|-------------------------------------------------|
| CR-T-01 | Atualizar KeyIndicators.tsx (icon, prop, label, valor) | —        | Card exibe "Gastos Planejados" com ClipboardList |
| CR-T-02 | Atualizar DashboardView.tsx (prop passada)           | CR-T-01    | Prop correta passada ao KeyIndicators            |
| CR-T-03 | Build TypeScript sem erros                           | CR-T-02    | `tsc --noEmit` passa                             |
| CR-T-04 | Atualizar documentação                               | CR-T-03    | Spec, CLAUDE.md e Plano refletem a mudança       |

---

## 8. Critérios de Aceite

- [ ] Card exibe label "Gastos Planejados" com ícone `ClipboardList`
- [ ] Card exibe valor de `total_despesas_planejadas` formatado em BRL
- [ ] Demais cards e gráficos do Dashboard inalterados
- [ ] Build TypeScript passa sem erros
- [ ] Documentos afetados atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral         | Probabilidade | Impacto | Mitigação                        |
|----|----------------------------------|---------------|---------|----------------------------------|
| 1  | Nenhum risco significativo       | —             | —       | Mudança puramente visual/frontend |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- **Método:** `git revert [hash]` — reverter o commit do CR-020
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard

### 10.2 Rollback de Migration
N/A — sem migrations.

### 10.3 Impacto em Dados
N/A — sem alterações em dados.

### 10.4 Rollback de Variáveis de Ambiente
N/A — sem variáveis novas/alteradas.

### 10.5 Verificação Pós-Rollback
- [ ] Card volta a exibir "Parcelas Futuras"

---

## Changelog

| Data       | Autor   | Descrição           |
|------------|---------|---------------------|
| 2026-03-13 | Claude  | CR criado           |
| 2026-03-13 | Claude  | Implementação concluída |
