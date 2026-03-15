# Change Request — CR-023: Remover status "Pendente" da projeção de parcelas

**Versão:** 1.0
**Data:** 2026-03-14
**Status:** Concluído
**Autor:** Claude
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Parcelamentos com 0 parcelas pagas recebem `status_badge = "Pendente"` e são excluídos da projeção 12 meses, gráfico empilhado e KPIs. No fluxo real do usuário, não existe o conceito de "ainda não começou" — todas as parcelas são criadas com vencimentos futuros definidos. Um parcelamento com 0 pagas simplesmente significa que a primeira parcela ainda não venceu, e deve aparecer na projeção normalmente.

**Exemplo:** Dois gastos "Receita Federal" (5x e 55x). O de 55x tem 0 pagas → status "Pendente" → R$ 0,00 na projeção, quando deveria mostrar ~R$ 143,53/mês pelos próximos 55 meses.

---

## 2. Classificação

| Campo            | Valor                           |
|------------------|---------------------------------|
| Tipo             | Bug Fix                         |
| Origem           | Feedback do usuário             |
| Urgência         | Próxima sprint                  |
| Complexidade     | Baixa                           |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
- `get_installment_projection()` atribui `status_badge = "Pendente"` quando `progresso == 0`
- Itens "Pendente" são excluídos de: projeção mensal (backend), KPIs (backend), gráfico empilhado (frontend)
- Gantt mostra itens "Pendente" com estilo tracejado cinza e texto "Pendente"

### Problema ou Necessidade
O conceito de "Pendente" (parcela que ainda não começou) não existe no fluxo do usuário. Todas as parcelas são criadas upfront com datas de vencimento futuras. Um parcelamento com 0 parcelas pagas é simplesmente um que ainda não teve nenhuma parcela vencida/paga, mas já tem compromisso financeiro real.

### Situação Desejada (TO-BE)
- Todo parcelamento com parcelas restantes > 0 recebe status "Ativa" ou "Encerrando" (≤ 2 restantes)
- Todos os parcelamentos aparecem na projeção mensal, gráfico empilhado e KPIs
- `mes_termino` é sempre calculado (nunca `None` para parcelamentos ativos)

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                           | Antes (AS-IS)                          | Depois (TO-BE)                        |
|----|--------------------------------|----------------------------------------|---------------------------------------|
| 1  | Status com 0 pagas             | `status_badge = "Pendente"`            | `status_badge = "Ativa"` ou `"Encerrando"` |
| 2  | `mes_termino` com 0 pagas      | `None`                                 | Calculado a partir do mês atual       |
| 3  | Projeção mensal                | Exclui itens Pendente                  | Inclui todos os parcelamentos ativos  |
| 4  | KPIs                           | Exclui itens Pendente dos totais       | Inclui todos os parcelamentos         |
| 5  | Gráfico empilhado              | Filtra itens Pendente                  | Mostra todos os parcelamentos         |
| 6  | Gantt                          | Estilo tracejado/cinza para Pendente   | Estilo normal (Ativa/Encerrando)      |

### 4.2 O que NÃO muda

- `ExpenseStatus.PENDENTE` (status de despesa individual Pago/Pendente/Atrasado) — completamente separado
- Lógica de agrupamento em `crud.get_installment_expenses_grouped()`
- Lógica de progresso do CR-022 (upfront vs incremental)
- Schema/endpoint `/api/installments/projection`

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas            | Ação Necessária          |
|-----------------------------------|------------|----------------------------|--------------------------|
| `/docs/01-PRD.md`                 | Não        | —                          | —                        |
| `/docs/02-ARCHITECTURE.md`        | Não        | —                          | —                        |
| `/docs/03-SPEC.md`                | Sim        | Projeção de parcelas       | Remover menção a "Pendente" |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim        | Visão geral CRs            | Adicionar CR-023         |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                          | —                        |
| `CLAUDE.md`                       | Sim        | Change Requests             | Adicionar CR-023         |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                              | Descrição da Mudança                          |
|-----------|-----------------------------------------------------------------|-----------------------------------------------|
| Modificar | `backend/app/services.py`                                       | Remover branch "Pendente" e filtros de exclusão |
| Modificar | `backend/app/schemas.py`                                        | Atualizar comentário de status_badge          |
| Modificar | `backend/tests/test_installment_projection.py`                  | Atualizar 2 testes que assertam "Pendente"    |
| Modificar | `frontend/src/types.ts`                                         | Remover "Pendente" do union type              |
| Modificar | `frontend/src/components/installments/ProjectionStackedChart.tsx`| Remover filtro de Pendente                    |
| Modificar | `frontend/src/components/installments/ProjectionGantt.tsx`      | Remover toda lógica isPending                 |
| Modificar | `frontend/src/pages/InstallmentsView.tsx`                       | Remover case "Pendente" do badge              |

### 6.2 Banco de Dados

Sem alterações no banco de dados. Sem migrations.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                                    | Depende de | Done When                              |
|---------|-----------------------------------------------------------|------------|----------------------------------------|
| CR-T-01 | Remover branch "Pendente" e filtros em services.py        | —          | Todos os parcelamentos incluídos na projeção |
| CR-T-02 | Atualizar comentário em schemas.py                        | CR-T-01    | Comentário reflete status válidos      |
| CR-T-03 | Atualizar testes test_installment_projection.py           | CR-T-01    | Testes passam com novo comportamento   |
| CR-T-04 | Remover "Pendente" do frontend (types, chart, gantt, view)| CR-T-01    | Build TypeScript passa sem erros       |
| CR-T-05 | Atualizar documentação                                    | CR-T-04    | Docs refletem a mudança                |

---

## 8. Critérios de Aceite

- [ ] Parcelamento com 0 parcelas pagas recebe status "Ativa" (ou "Encerrando" se ≤ 2 restantes)
- [ ] Parcelamento com 0 parcelas pagas aparece no gráfico de projeção 12 meses
- [ ] KPIs incluem todos os parcelamentos nos totais
- [ ] `mes_termino` nunca é `None` para parcelamentos ativos
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a mudança
- [ ] Documentos afetados foram atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral              | Probabilidade | Impacto | Mitigação                               |
|----|---------------------------------------|---------------|---------|------------------------------------------|
| 1  | KPIs mostram valores maiores que antes | Alta          | Baixo   | Comportamento correto — antes excluía dados válidos |

---

## 10. Plano de Rollback

### 10.1 Rollback de Código
- **Método:** `git revert [hash]` → merge em `master` → push
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard

### 10.2 Rollback de Migration
- N/A — sem migrations neste CR

### 10.3 Impacto em Dados
- N/A — sem alterações no banco

### 10.4 Rollback de Variáveis de Ambiente
- N/A — nenhuma variável nova/alterada

### 10.5 Verificação Pós-Rollback
- [ ] Aplicação acessível e funcional
- [ ] Gráfico de projeção renderiza corretamente
- [ ] Usuários existentes conseguem fazer login

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-03-14 | Claude | CR criado                    |
| 2026-03-14 | Claude | Implementação concluída      |
