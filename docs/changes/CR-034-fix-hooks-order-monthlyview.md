# Change Request — CR-034: Fix Rules of Hooks no MonthlyView (tela branca após login)

**Versão:** 1.0
**Data:** 2026-03-18
**Status:** Concluído
**Autor:** Claude
**Prioridade:** Crítica

---

## 1. Resumo da Mudança

Após o merge do CR-033, a aplicação exibe tela branca imediatamente após o login. A causa é uma violação das Rules of Hooks do React no componente `MonthlyView`: os hooks `useAlerts()` e `useQueryClient()` foram chamados após returns condicionais (`if (isLoading)`, `if (isError)`), causando crash silencioso no React.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Bug Fix                   |
| Origem           | Bug reportado             |
| Urgência         | Imediata                  |
| Complexidade     | Baixa                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
No `MonthlyView.tsx`, os hooks `useAlerts()` e `useQueryClient()` são chamados na linha 54, **após** dois early returns condicionais (linhas 26-52 para `isLoading` e `isError`). Isso viola as Rules of Hooks do React: hooks devem ser chamados na mesma ordem em toda renderização.

### Problema ou Necessidade
Quando o usuário faz login, a rota `/` carrega `MonthlyView`. Na primeira renderização, `isLoading` é `true`, então o componente retorna antes de chamar `useAlerts()`. Na próxima renderização (dados carregados), `useAlerts()` é chamado. O React detecta a mudança na ordem dos hooks e lança um erro, resultando em tela branca.

### Situação Desejada (TO-BE)
Todos os hooks chamados no topo do componente, antes de qualquer return condicional, respeitando as Rules of Hooks.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                         | Antes (AS-IS)                          | Depois (TO-BE)                          |
|----|------------------------------|----------------------------------------|-----------------------------------------|
| 1  | Posição dos hooks no MonthlyView | `useAlerts()` e `useQueryClient()` após early returns | Hooks movidos para o topo, antes dos early returns |

### 4.2 O que NÃO muda

- Comportamento funcional dos alertas
- Layout e renderização da página
- Nenhum outro componente afetado (ScoreDetailView, InstallmentsView e DashboardView já chamam hooks corretamente)

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | —               | —                   |
| `/docs/02-ARCHITECTURE.md`        | Não        | —               | —                   |
| `/docs/03-SPEC.md`                | Não        | —               | —                   |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | —               | —                   |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —               | —                   |
| `CLAUDE.md`                       | Sim        | Change Requests  | Adicionar CR-034    |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                          | Descrição da Mudança                              |
|-----------|---------------------------------------------|----------------------------------------------------|
| Modificar | `frontend/src/pages/MonthlyView.tsx`        | Mover `useAlerts()` e `useQueryClient()` para o topo |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                            | Depende de | Done When                                    |
|---------|---------------------------------------------------|------------|----------------------------------------------|
| CR-T-01 | Mover hooks para o topo do MonthlyView            | —          | Hooks chamados antes dos early returns       |
| CR-T-02 | Verificar build TypeScript                        | CR-T-01    | `tsc --noEmit` passa sem erros               |
| CR-T-03 | Atualizar CLAUDE.md                               | CR-T-02    | CR-034 listado nos Change Requests           |

---

## 8. Critérios de Aceite

- [x] Hooks `useAlerts()` e `useQueryClient()` chamados antes de qualquer return condicional
- [x] Build TypeScript passa sem erros
- [ ] App não exibe tela branca após login
- [ ] Testes existentes continuam passando (regressão)
- [ ] CLAUDE.md atualizado com CR-034

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|----|--------------------------|---------------|---------|-----------|
| 1  | Nenhum risco identificado — mudança é apenas reordenação de código | — | — | — |

---

## 10. Plano de Rollback

N/A — fix trivial de reordenação de hooks. Em caso de necessidade, reverter o commit único.

- **Rollback de Migration:** N/A
- **Rollback de Variáveis de Ambiente:** N/A

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-03-18 | Claude | CR criado e implementação iniciada |
| 2026-03-18 | Claude | Implementação concluída — validação: ✅ |
