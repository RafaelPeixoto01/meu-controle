# Change Request — CR-028: Fix badge "Encerrando" duplicado em parcelas com mesmo nome

**Versão:** 1.0
**Data:** 2026-03-16
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Média

---

## 1. Resumo da Mudança

Corrigir bug na aba de Compras Parceladas onde dois parcelamentos com o mesmo nome mas `parcela_total` diferente (ex: "Receita Federal" 5x e "Receita Federal" 55x) mostram ambos o badge "Encerrando" e a mesma data de término, quando apenas o que realmente está encerrando deveria exibir esse badge.

---

## 2. Classificação

| Campo            | Valor                    |
|------------------|--------------------------|
| Tipo             | Bug Fix                  |
| Origem           | Bug reportado            |
| Urgência         | Próxima sprint           |
| Complexidade     | Baixa                    |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O frontend faz lookup da projeção de parcelas usando apenas o campo `nome`:
```tsx
projectionData?.find((p) => p.nome === group.nome)
```
Quando dois grupos têm o mesmo nome mas `parcela_total` diferente, `Array.find()` retorna o primeiro match para ambos, propagando badge e `mes_termino` incorretos.

### Problema ou Necessidade
Dois parcelamentos "Receita Federal" (5x e 55x) mostram ambos "Encerrando" e "Termina em Mar/2026", quando o de 55x deveria mostrar "Ativa" com data de término diferente.

### Situação Desejada (TO-BE)
Cada grupo de parcelamento recebe os dados de projeção corretos, usando `nome` + `parcela_total` como chave de lookup.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                              | Antes (AS-IS)                        | Depois (TO-BE)                                    |
|----|-----------------------------------|--------------------------------------|---------------------------------------------------|
| 1  | Lookup de projeção                | Match por `nome` apenas              | Match por `nome` + `parcela_total`                |
| 2  | Tipo inline de projectionData     | Sem campo `parcela_total`            | Inclui campo `parcela_total: number`              |

### 4.2 O que NÃO muda

- Backend (services.py, crud.py) — projeção já retorna `parcela_total` por item
- Tipos TypeScript (`InstallmentProjectionItem`) — já tem `parcela_total`
- Componentes de projeção (Gantt, Charts)
- Lógica de agrupamento no backend

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária       |
|-----------------------------------|------------|------------------|-----------------------|
| `/docs/01-PRD.md`                 | Não        | —                | —                     |
| `/docs/02-ARCHITECTURE.md`       | Não        | —                | —                     |
| `/docs/03-SPEC.md`               | Não        | —                | —                     |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim        | Visão Geral      | Adicionar ref CR-028  |
| `/docs/05-DEPLOY-GUIDE.md`       | Não        | —                | —                     |
| `CLAUDE.md`                       | Sim        | Change Requests  | Adicionar CR-028      |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                              | Descrição da Mudança                                           |
|-----------|------------------------------------------------|----------------------------------------------------------------|
| Modificar | `frontend/src/pages/InstallmentsView.tsx`       | Lookup por `nome` + `parcela_total`; adicionar `parcela_total` ao tipo inline |

### 6.2 Banco de Dados

N/A — sem alterações no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                                          | Depende de | Done When                                        |
|---------|-----------------------------------------------------------------|------------|--------------------------------------------------|
| CR-T-01 | Corrigir lookup de projeção por `nome` + `parcela_total`        | —          | Cada grupo recebe projeção correta               |
| CR-T-02 | Verificar outros lookups por nome no arquivo                    | CR-T-01    | Nenhum outro lookup vulnerável encontrado         |
| CR-T-03 | Build TypeScript                                                | CR-T-01    | `tsc --noEmit` passa sem erros                   |
| CR-T-04 | Criar CR doc + atualizar docs                                   | CR-T-03    | Docs refletem a mudança                          |
| CR-T-05 | Commit, merge e push                                            | CR-T-04    | Branch merged em master                          |

---

## 8. Critérios de Aceite

- [x] Parcelamentos com mesmo nome mas `parcela_total` diferente mostram badges corretos
- [x] Cada grupo exibe sua data de término correta
- [x] Build TypeScript passa sem erros
- [x] Testes existentes continuam passando (regressão)
- [x] Documentos afetados foram atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | Nenhum risco identificado          | —             | —       | Mudança isolada no frontend      |

---

## 10. Plano de Rollback

N/A — mudança trivial de UI, revert de commit único é suficiente.

---

## Changelog

| Data       | Autor   | Descrição                    |
|------------|---------|------------------------------|
| 2026-03-16 | Rafael  | CR criado e implementado     |
