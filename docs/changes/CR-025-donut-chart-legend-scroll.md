# Change Request — CR-025: Remover scroll das legendas dos donut charts no Dashboard

**Versão:** 1.0
**Data:** 2026-03-16
**Status:** Concluído
**Autor:** Rafael
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

Os gráficos "Despesas Planejadas por Categoria" e "Gastos Diários por Categoria" no Dashboard têm legendas com altura máxima fixa (`max-h-40 = 160px`) e `overflow-y-auto`, causando scroll quando há muitas categorias. A mudança remove essas restrições para que a legenda cresça naturalmente conforme a quantidade de categorias.

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
A legenda customizada do `CategoryDonutChart` tem `max-h-40 overflow-y-auto`, limitando a 160px de altura. Quando há mais de ~5 categorias, parte da legenda fica oculta e o usuário precisa usar scroll para ver todas.

### Problema ou Necessidade
Scroll na legenda dificulta a visualização rápida de todas as categorias. O componente deveria se adequar à quantidade de informação.

### Situação Desejada (TO-BE)
A legenda exibe todas as categorias sem scroll, crescendo verticalmente conforme necessário.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                     | Antes (AS-IS)                              | Depois (TO-BE)          |
|----|--------------------------|--------------------------------------------|-------------------------|
| 1  | Classe CSS da legenda    | `max-h-40 overflow-y-auto`                 | Sem restrição de altura |

### 4.2 O que NÃO muda

- Estrutura da legenda (cor, nome, percentual, valor)
- Gráfico donut em si
- Tooltip
- Layout do DashboardView

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária          |
|-----------------------------------|------------|-----------------|--------------------------|
| `/docs/01-PRD.md`                 | Não        | —               | —                        |
| `/docs/02-ARCHITECTURE.md`        | Não        | —               | —                        |
| `/docs/03-SPEC.md`                | Não        | —               | —                        |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | —               | —                        |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —               | —                        |
| `CLAUDE.md`                       | Sim        | Change Requests  | Adicionar CR-025         |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                                  | Descrição da Mudança                          |
|-----------|---------------------------------------------------------------------|-----------------------------------------------|
| Modificar | `frontend/src/components/dashboard/CategoryDonutChart.tsx`          | Remover `max-h-40 overflow-y-auto` da legenda |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                              | Depende de | Done When                                    |
|---------|-----------------------------------------------------|------------|----------------------------------------------|
| CR-T-01 | Remover `max-h-40 overflow-y-auto` da legenda       | —          | Legenda cresce sem scroll                    |
| CR-T-02 | Verificar build TypeScript                          | CR-T-01    | `tsc --noEmit` passa sem erros               |
| CR-T-03 | Atualizar CLAUDE.md                                 | CR-T-02    | CR-025 listado nos Change Requests           |

---

## 8. Critérios de Aceite

- [ ] Legendas dos donut charts exibem todas as categorias sem scroll
- [ ] Build TypeScript passa sem erros
- [ ] Documentos atualizados (CLAUDE.md)

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                    | Probabilidade | Impacto | Mitigação               |
|----|---------------------------------------------|---------------|---------|-------------------------|
| 1  | Cards ficam mais altos com muitas categorias| Baixa         | Baixo   | Aceitável — melhor UX   |

---

## 10. Plano de Rollback

N/A — mudança CSS trivial, revertível com `git revert`.

---

## Changelog

| Data       | Autor  | Descrição              |
|------------|--------|------------------------|
| 2026-03-16 | Rafael | CR criado              |
| 2026-03-16 | Rafael | Implementação concluída |
