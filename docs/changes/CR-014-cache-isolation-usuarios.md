# Change Request — CR-014: Isolamento de Cache entre Usuarios

**Versao:** 1.0
**Data:** 2026-03-06
**Status:** Concluido
**Autor:** Rafael
**Prioridade:** Critica

---

## 1. Resumo da Mudanca

Bug critico de seguranca: ao fazer login com usuario A (Google OAuth) e depois logout + login com usuario B (email/senha), o usuario B ve os dados do usuario A. A causa raiz e que o cache do TanStack Query nao e limpo no logout/login, e as cache keys nao incluem o user ID — dados de usuarios diferentes compartilham o mesmo namespace de cache.

---

## 2. Classificacao

| Campo            | Valor                    |
|------------------|--------------------------|
| Tipo             | Bug Fix (Seguranca)      |
| Origem           | Bug reportado             |
| Urgencia         | Imediata                  |
| Complexidade     | Media                     |

---

## 3. Contexto e Motivacao

### Situacao Atual (AS-IS)
- `logout()` em AuthContext limpa apenas localStorage e user state, mas NAO limpa o cache do TanStack Query
- Cache keys sao genericas (ex: `["monthly-summary", year, month]`) sem user ID
- QueryClient inacessivel do AuthContext
- staleTime de 5 min mantem dados do usuario anterior em memoria

### Problema ou Necessidade
Quando usuario A faz login, visualiza dados e faz logout, o usuario B que faz login em seguida ve os dados de A porque o cache do TanStack Query serve dados stale do usuario anterior.

### Situacao Desejada (TO-BE)
- Cache do TanStack Query limpo em todo logout e login
- Cache keys incluem user ID como defesa em profundidade
- Impossivel ver dados de outro usuario mesmo com cache em memoria

---

## 4. Detalhamento da Mudanca

### 4.1 O que muda

| #  | Item                          | Antes (AS-IS)                              | Depois (TO-BE)                                      |
|----|-------------------------------|--------------------------------------------|-----------------------------------------------------|
| 1  | queryClient em main.tsx       | Variavel local, nao exportada              | Exportada para uso no AuthContext                    |
| 2  | logout() em AuthContext       | Limpa apenas localStorage e user state     | Tambem chama queryClient.clear()                     |
| 3  | login/register/loginWithGoogle| Nao limpa cache                            | Chama queryClient.clear() antes de setar novo usuario|
| 4  | Cache keys (todos os hooks)   | Genericas sem user ID                      | Incluem user ID como prefixo                         |

### 4.2 O que NAO muda

- Backend (todas as queries ja filtram por user_id corretamente)
- Logica de autenticacao (JWT, Google OAuth, refresh tokens)
- Estrutura de componentes
- Funcionalidade de CRUD

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Secoes Afetadas | Acao Necessaria          |
|-----------------------------------|------------|-----------------|--------------------------|
| `/docs/01-PRD.md`                 | Nao        | —               | —                        |
| `/docs/02-ARCHITECTURE.md`        | Nao        | —               | —                        |
| `/docs/03-SPEC.md`                | Nao        | —               | —                        |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Nao        | —               | —                        |
| `/docs/05-DEPLOY-GUIDE.md`        | Nao        | —               | —                        |
| `CLAUDE.md`                       | Sim        | CRs concluidos  | Adicionar CR-014         |

---

## 6. Impacto no Codigo

### 6.1 Arquivos Afetados

| Acao      | Caminho do Arquivo                                | Descricao da Mudanca                                    |
|-----------|---------------------------------------------------|---------------------------------------------------------|
| Modificar | `frontend/src/main.tsx`                           | Exportar queryClient                                    |
| Modificar | `frontend/src/contexts/AuthContext.tsx`            | Importar queryClient, chamar clear() no logout e login  |
| Modificar | `frontend/src/hooks/useMonthTransition.ts`        | Adicionar userId na cache key                           |
| Modificar | `frontend/src/hooks/useExpenses.ts`               | Sem mudanca em cache keys (usa apenas mutations)        |
| Modificar | `frontend/src/hooks/useIncomes.ts`                | Sem mudanca em cache keys (usa apenas mutations)        |
| Modificar | `frontend/src/hooks/useDailyExpenses.ts`          | Adicionar userId nas cache keys                         |
| Modificar | `frontend/src/pages/InstallmentsView.tsx`         | Adicionar userId na cache key                           |

### 6.2 Banco de Dados

Nenhum impacto.

---

## 7. Tarefas de Implementacao

| ID      | Tarefa                                              | Depende de | Done When                                          |
|---------|-----------------------------------------------------|------------|-----------------------------------------------------|
| CR-T-01 | Exportar queryClient de main.tsx                    | —          | queryClient acessivel fora do modulo                |
| CR-T-02 | Limpar cache no logout e login (AuthContext)        | CR-T-01    | queryClient.clear() chamado em toda troca de usuario|
| CR-T-03 | Adicionar userId nas cache keys de todos os hooks   | CR-T-02    | Todas as cache keys incluem userId                  |
| CR-T-04 | Verificar build TypeScript                          | CR-T-03    | `tsc --noEmit` passa sem erros                      |
| CR-T-05 | Atualizar CLAUDE.md                                 | CR-T-04    | CR-014 listado nos CRs concluidos                   |

---

## 8. Criterios de Aceite

- [ ] Login com usuario A, ver dados, logout, login com usuario B → ve dados de B
- [ ] Cache limpo em todo logout (queryClient.clear() chamado)
- [ ] Cache limpo em todo login (queryClient.clear() chamado antes de setar usuario)
- [ ] Cache keys incluem userId em todos os hooks com useQuery
- [ ] Build TypeScript passa sem erros
- [ ] Testes existentes continuam passando (regressao)

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                              | Probabilidade | Impacto | Mitigacao                                  |
|----|-------------------------------------------------------|---------------|---------|---------------------------------------------|
| 1  | Re-fetch de dados apos login (cache limpo)            | Certa         | Baixo   | Comportamento esperado e correto            |
| 2  | Flash de loading ao trocar usuario                     | Alta          | Baixo   | UX aceitavel — seguranca > performance      |

---

## 10. Plano de Rollback

### 10.1 Rollback de Codigo

- **Metodo:** `git revert [hash]` → merge em `master` → push
- Mudanca e frontend-only, rollback trivial

### 10.2 Rollback de Migration

Nao aplicavel.

### 10.3 Impacto em Dados

Nao aplicavel.

### 10.4 Rollback de Variaveis de Ambiente

Nenhuma.

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] Usuarios conseguem fazer login

---

## Changelog

| Data       | Autor  | Descricao                    |
|------------|--------|------------------------------|
| 2026-03-06 | Rafael | CR criado e implementado     |
