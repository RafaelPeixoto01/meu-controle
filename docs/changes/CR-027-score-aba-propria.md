# Change Request — CR-027: Mover Score para aba propria no ViewSelector

**Versao:** 1.0
**Data:** 2026-03-16
**Status:** Concluido
**Autor:** Rafael
**Prioridade:** Media

---

## 1. Resumo da Mudanca

O card de Score de Saude Financeira (CR-026) integrado no Dashboard nao ficou bom visualmente. Mover o score para uma aba propria no ViewSelector ("Score") e restaurar o Dashboard ao visual anterior (sem card de score).

---

## 2. Classificacao

| Campo            | Valor                              |
|------------------|------------------------------------|
| Tipo             | Mudanca de Regra de Negocio        |
| Origem           | Feedback do usuario                |
| Urgencia         | Proxima sprint                     |
| Complexidade     | Baixa                              |

---

## 3. Contexto e Motivacao

### Situacao Atual (AS-IS)
- Dashboard exibe um ScoreGauge compact antes dos KPI cards
- Score detalhado so e acessivel via click no card compact do Dashboard
- ViewSelector tem 4 abas: Dashboard, Gastos Planejados, Gastos Diarios, Parcelas

### Problema ou Necessidade
O card de score dentro do Dashboard nao ficou bom visualmente. O score merece sua propria aba para melhor acessibilidade.

### Situacao Desejada (TO-BE)
- Dashboard volta ao visual pre-CR-026 (sem card de score)
- ViewSelector ganha 5a aba: "Score" apontando para `/score`
- ScoreDetailView (ja existente) acessivel diretamente pela aba

---

## 4. Detalhamento da Mudanca

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)                     | Depois (TO-BE)                    |
|----|-------------------------|-----------------------------------|-----------------------------------|
| 1  | Dashboard               | Exibe ScoreGauge compact no topo  | Nao exibe score (visual pre-CR-026) |
| 2  | ViewSelector            | 4 abas                           | 5 abas (+ "Score")               |
| 3  | Acesso ao score         | Via card no Dashboard             | Via aba "Score" no ViewSelector   |

### 4.2 O que NAO muda

- ScoreDetailView (pagina `/score`) permanece identica
- Rota `/score` em App.tsx permanece identica
- Backend (endpoints, calculo, persistencia) nao e afetado
- Componentes score/ (ScoreGauge, ScoreDimensionBreakdown, etc.) nao sao afetados

---

## 5. Impacto nos Documentos

| Documento                       | Impactado? | Secoes Afetadas              | Acao Necessaria       |
|---------------------------------|------------|------------------------------|-----------------------|
| `/docs/01-PRD.md`               | Nao        | —                            | —                     |
| `/docs/02-ARCHITECTURE.md`      | Nao        | —                            | —                     |
| `/docs/03-SPEC.md`              | Sim        | Secao F04                    | Atualizar: score e aba, nao card |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim      | Visao Geral                  | Adicionar CR-027      |
| `/docs/05-DEPLOY-GUIDE.md`      | Nao        | —                            | —                     |
| `CLAUDE.md`                      | Sim        | CRs, ultima tarefa           | Adicionar CR-027      |

---

## 6. Impacto no Codigo

### 6.1 Arquivos Afetados

| Acao      | Caminho do Arquivo                               | Descricao da Mudanca               |
|-----------|--------------------------------------------------|-------------------------------------|
| Modificar | `frontend/src/pages/DashboardView.tsx`           | Remover ScoreGauge e useHealthScore |
| Modificar | `frontend/src/components/ViewSelector.tsx`        | Adicionar 5a aba "Score"            |

### 6.2 Banco de Dados

N/A — sem mudancas de banco.

---

## 7. Tarefas de Implementacao

| ID       | Tarefa                              | Depende de | Done When                          |
|----------|-------------------------------------|------------|------------------------------------|
| CR27-T-01 | Remover ScoreGauge do DashboardView | —          | Dashboard sem card de score        |
| CR27-T-02 | Adicionar aba Score no ViewSelector | —          | 5 abas visiveis, navegacao funciona |
| CR27-T-03 | Atualizar documentacao              | CR27-T-01~02 | Docs refletem mudanca            |

---

## 8. Criterios de Aceite

- [ ] Dashboard nao exibe card de score (visual pre-CR-026)
- [ ] ViewSelector mostra 5 abas incluindo "Score"
- [ ] Clicar em "Score" navega para `/score` com conteudo completo
- [ ] 5 abas cabem no mobile com scroll horizontal
- [ ] TypeScript build passa sem erros
- [ ] Documentos afetados atualizados

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigacao                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | 5 abas podem ficar apertadas no mobile | Baixa     | Baixo   | overflow-x-auto ja existe no ViewSelector |

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo
- **Metodo:** `git revert [hash]` → merge em `master` → push
- **Commits a reverter:** 1 commit (frontend + docs)

### 10.2-10.4
N/A — sem migration, sem dados, sem variaveis.

### 10.5 Verificacao Pos-Rollback
- [ ] Dashboard exibe card de score novamente
- [ ] ViewSelector volta a 4 abas

---

## Changelog

| Data       | Autor   | Descricao                    |
|------------|---------|------------------------------|
| 2026-03-16 | Claude  | CR criado                    |
| 2026-03-16 | Claude  | Implementacao concluida      |
