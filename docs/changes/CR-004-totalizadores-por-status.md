# Change Request — CR-004: Totalizadores de Despesa por Status

**Versão:** 1.0
**Data:** 2026-02-11
**Status:** Aprovado
**Autor:** Rafael
**Prioridade:** Média

---

## 1. Resumo da Mudança

Adicionar três novos totalizadores na visão mensal que decompõem o total de despesas por status de pagamento: **Pago**, **Pendente** e **Atrasado**. Os valores são exibidos no footer da tabela de despesas, acima da linha "Total Despesas" existente, usando as cores do Design System. Os totalizadores são calculados no backend e retornados como campos adicionais na resposta `MonthlySummary`.

---

## 2. Classificação

| Campo            | Valor              |
|------------------|--------------------|
| Tipo             | Nova Feature       |
| Origem           | Evolução do produto |
| Urgência         | Próxima sprint     |
| Complexidade     | Baixa              |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

A visão mensal (`GET /api/months/{year}/{month}`) retorna três totalizadores:
- `total_despesas`: soma de **todas** as despesas do mês, independente do status
- `total_receitas`: soma de todas as receitas do mês
- `saldo_livre`: `total_receitas - total_despesas`

O usuário vê apenas o total geral de despesas e não tem visibilidade rápida de quanto já pagou, quanto falta pagar e quanto está atrasado.

### Problema ou Necessidade

Para tomar decisões financeiras no mês, o usuário precisa saber rapidamente:
- Quanto já saiu da conta (Pago)
- Quanto ainda vai sair (Pendente)
- Quanto está em atraso e precisa de atenção imediata (Atrasado)

Atualmente, essa informação só é obtida analisando despesa por despesa na tabela.

### Situação Desejada (TO-BE)

A API retorna 3 campos adicionais na `MonthlySummary`: `total_pago`, `total_pendente`, `total_atrasado`. O frontend exibe esses valores como linhas de resumo coloridas no footer da tabela de despesas, logo acima da linha "Total Despesas". A invariante `total_pago + total_pendente + total_atrasado == total_despesas` é sempre mantida.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|---------------|----------------|
| 1  | Schema `MonthlySummary` (backend) | 6 campos: `mes_referencia`, `total_despesas`, `total_receitas`, `saldo_livre`, `expenses`, `incomes` | 9 campos: adicionados `total_pago`, `total_pendente`, `total_atrasado` (float, entre `saldo_livre` e `expenses`) |
| 2  | Cálculo em `services.py` | `get_monthly_summary` calcula apenas `total_despesas` (soma geral) | Calcula adicionalmente 3 somas filtradas por `expense.status` |
| 3  | Type `MonthlySummary` (frontend) | Espelha os 6 campos do backend | Espelha os 9 campos, incluindo `total_pago`, `total_pendente`, `total_atrasado` |
| 4  | Footer da `ExpenseTable` | Uma única linha: "Total Despesas" com valor formatado em BRL | 4 linhas: 3 linhas de status (Pago/Pendente/Atrasado com cores) + 1 linha "Total Despesas" (inalterada) |
| 5  | Props de `ExpenseTable` | Recebe `totalDespesas` | Recebe adicionalmente `totalPago`, `totalPendente`, `totalAtrasado` |
| 6  | `MonthlyView.tsx` | Passa `data.total_despesas` para `ExpenseTable` | Passa adicionalmente `data.total_pago`, `data.total_pendente`, `data.total_atrasado` |
| 7  | RF-04 no PRD | "Exibir totalizadores: total despesas, total receitas e saldo livre" | Adiciona: "total por status (Pago, Pendente, Atrasado)" |

### 4.2 O que NÃO muda

- **Saldo livre:** Cálculo permanece `total_receitas - total_despesas` (RN-009)
- **Banco de dados:** Nenhuma alteração de schema, sem migration necessária
- **Routers/Endpoints:** Mesma rota `GET /api/months/{year}/{month}`, resposta estendida (aditiva)
- **CRUD functions:** Nenhuma alteração em `crud.py`
- **Models:** Nenhuma alteração em `models.py`
- **SaldoLivre component:** Inalterado
- **IncomeTable component:** Inalterado
- **Autenticação:** Nenhuma alteração (endpoints continuam protegidos)
- **Transição de mês (RF-06):** Inalterada
- **Auto-detecção de status (RF-05):** Inalterada (os novos totais são calculados *depois* da auto-detecção)

---

## 5. Impacto nos Documentos

| Documento | Impactado? | Seções Afetadas | Ação Necessária |
|-----------|------------|-----------------|-----------------|
| `/docs/01-PRD.md` | Sim | RF-04 (Totalizadores) | Adicionar menção aos totalizadores por status |
| `/docs/02-ARCHITECTURE.md` | Não | — | — |
| `/docs/03-SPEC.md` | Sim | Feature RF-03/RF-04 (schemas, services, types, ExpenseTable) | Atualizar MonthlySummary schema, services.py, types.ts, ExpenseTable footer |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Novo grupo CR-004 | Adicionar tarefas de implementação |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação | Caminho do Arquivo | Descrição da Mudança |
|------|-------------------|----------------------|
| Modificar | `backend/app/schemas.py` | Adicionar 3 campos `float` à classe `MonthlySummary`: `total_pago`, `total_pendente`, `total_atrasado` |
| Modificar | `backend/app/services.py` | Calcular 3 somas por status em `get_monthly_summary()`, após `apply_status_auto_detection` |
| Modificar | `frontend/src/types.ts` | Espelhar 3 novos campos no interface `MonthlySummary` |
| Modificar | `frontend/src/pages/MonthlyView.tsx` | Passar `totalPago`, `totalPendente`, `totalAtrasado` como props para `ExpenseTable` |
| Modificar | `frontend/src/components/ExpenseTable.tsx` | Atualizar interface de props + renderizar 3 linhas de resumo no `<tfoot>` |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|----------------------|
| Nenhuma | Totalizadores são calculados em runtime, não armazenados | Não |

---

## 7. Tarefas de Implementação

| ID | Tarefa | Arquivos | Depende de | Done When |
|----|--------|----------|------------|-----------|
| CR4-T-01 | Adicionar campos `total_pago`, `total_pendente`, `total_atrasado` ao schema `MonthlySummary` | `backend/app/schemas.py` | — | Schema compila com 3 novos campos `float` |
| CR4-T-02 | Calcular totais por status em `get_monthly_summary` | `backend/app/services.py` | CR4-T-01 | Swagger UI mostra os 3 novos campos com valores corretos na resposta de `GET /api/months/{y}/{m}` |
| CR4-T-03 | Adicionar campos ao type `MonthlySummary` no frontend | `frontend/src/types.ts` | CR4-T-01 | `npm run build` compila sem erros |
| CR4-T-04 | Passar novos totais como props para `ExpenseTable` | `frontend/src/pages/MonthlyView.tsx` | CR4-T-03 | Props passadas corretamente, sem erros TS |
| CR4-T-05 | Renderizar linhas de resumo por status no footer da tabela de despesas | `frontend/src/components/ExpenseTable.tsx` | CR4-T-04 | 3 linhas coloridas (Pago/Pendente/Atrasado) aparecem acima de "Total Despesas" com valores BRL |
| CR4-T-06 | Atualizar documentos afetados (PRD, Spec, Plano de Implementação) | `docs/01-PRD.md`, `docs/03-SPEC.md`, `docs/04-IMPLEMENTATION-PLAN.md` | CR4-T-05 | Docs refletem os novos totalizadores |

---

## 8. Critérios de Aceite

- [ ] API `GET /api/months/{year}/{month}` retorna `total_pago`, `total_pendente`, `total_atrasado` na resposta JSON
- [ ] Invariante: `total_pago + total_pendente + total_atrasado == total_despesas` (sempre)
- [ ] Os 3 valores são `0.0` quando não há despesas no mês
- [ ] Os valores são recalculados corretamente após auto-detecção de status (RF-05)
- [ ] Footer da tabela de despesas exibe 3 linhas coloridas acima do "Total Despesas":
  - Pago: cor verde (tokens `pago`/`pago-bg` do Design System)
  - Pendente: cor amarela (tokens `pendente`/`pendente-bg`)
  - Atrasado: cor vermelha (tokens `atrasado`/`atrasado-bg`)
- [ ] Valores formatados em BRL (R$ X.XXX,XX)
- [ ] Ao alterar status de uma despesa (click no badge), os totais são atualizados após refetch
- [ ] Saldo livre permanece inalterado (total_receitas - total_despesas)
- [ ] `npm run build` compila sem erros TypeScript
- [ ] Backend inicia sem erros (`uvicorn app.main:app --reload`)
- [ ] Documentos afetados foram atualizados (PRD, Spec, Plano)

---

## 9. Riscos e Efeitos Colaterais

| # | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|---|--------------------------|---------------|---------|-----------|
| 1 | Resposta JSON maior (3 campos float adicionais) | Certa | Baixo | Impacto desprezível: 3 floats adicionam ~60 bytes ao payload. Irrelevante para < 100 lançamentos |
| 2 | Inconsistência temporária: `total_pago + total_pendente + total_atrasado != total_despesas` | Baixa | Médio | O cálculo é feito no mesmo loop, após status auto-detection. Arredondar com `round(x, 2)` em todos os campos |
| 3 | Frontend antigo em cache não espera os novos campos | Baixa | Baixo | Mudança é aditiva — campos extras no JSON são ignorados por browsers/TanStack Query. Nenhuma incompatibilidade |

---

## 10. Plano de Rollback

> Referência: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (seções 4 e 5).

### 10.1 Rollback de Código

- **Método:** `git revert [hash(es)]` + push para `master` (Railway auto-deploy)
- **Método alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** Commit(s) do CR-004

### 10.2 Rollback de Migration

- **Migration afetada:** Nenhuma — CR-004 não envolve alteração de schema de banco
- **Comando de downgrade:** N/A
- **Downgrade testado?** N/A
- **Downgrade é destrutivo?** N/A

### 10.3 Impacto em Dados

- **Dados serão perdidos no rollback?** [x] Não
- **Detalhamento:** Nenhum dado é armazenado — totais são calculados em runtime a partir de dados existentes
- **Backup necessário antes do deploy?** [x] Não

### 10.4 Rollback de Variáveis de Ambiente

- **Variáveis novas/alteradas:** Nenhuma

### 10.5 Verificação Pós-Rollback

- [ ] Aplicação acessível e funcional
- [ ] `GET /api/months/{y}/{m}` retorna `MonthlySummary` sem os campos de status (formato anterior)
- [ ] Frontend renderiza tabela de despesas com footer original (apenas "Total Despesas")
- [ ] Usuários existentes conseguem fazer login

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-02-11 | Rafael | CR criado |
