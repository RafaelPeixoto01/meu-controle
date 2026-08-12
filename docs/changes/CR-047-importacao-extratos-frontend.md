# Change Request — CR-047: Importação de Extratos e Faturas — Frontend (F07)

**Versão:** 1.0
**Data:** 2026-08-12
**Status:** Em Implementação
**Autor:** Rafael (via Claude)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Entregar a UI da feature **F07 — Importação de Extratos e Faturas (PDF)**: página própria "Importar" no ViewSelector com o fluxo **upload → processando → revisão → resultado**, consumindo a API `/api/imports` entregue no CR-046. Inclui o caminho `FormData` no client HTTP (`services/api.ts`) mantendo a injeção de Bearer token e o interceptor de refresh-401.

> Spec: `docs/specs/10-importacao-extratos.md` (F07, RF-21, US-29). Design aprovado no plano de brainstorming de 2026-08-12.

---

## 2. Classificação

| Campo            | Valor                          |
|------------------|--------------------------------|
| Tipo             | Nova Feature (UI)              |
| Origem           | Evolução do produto            |
| Urgência         | Próxima sprint                 |
| Complexidade     | Média                          |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O backend de importação (CR-046) está no ar, mas não há interface: os endpoints só são acessíveis via HTTP direto. O client `api.ts` só fala JSON (`Content-Type: application/json` fixo), sem suporte a multipart.

### Problema ou Necessidade
Sem UI, a feature não tem valor para o usuário final.

### Situação Desejada (TO-BE)
Aba "Importar" no ViewSelector → página `/import`: selecionar PDF → acompanhar processamento (IA pode levar até ~90s) → revisar transações agrupadas por classificação (novos gastos / conciliações / ignoradas / duplicadas) com edição inline e seleção → confirmar → ver resumo do resultado. Lotes pendentes de revisão são oferecidos para retomada ao entrar na página.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)        | Depois (TO-BE)       |
|----|-------------------------|----------------------|----------------------|
| 1  | Navegação               | 5 abas no ViewSelector | 6 abas (+ "Importar" → `/import`) |
| 2  | Client HTTP             | Só JSON              | + `requestMultipart` (FormData, sem Content-Type manual, mesmo Bearer + refresh-401) |
| 3  | Entrada de dados        | Digitação manual     | Upload de PDF com revisão antes de gravar |
| 4  | Cache TanStack Query    | —                    | Confirmação invalida `daily-expenses-summary` e `monthly-summary` (expenses) |

### 4.2 O que NÃO muda

- Backend — nenhum endpoint novo ou alterado (contrato do CR-046 consumido como está)
- Fluxos existentes de CRUD manual (gastos diários/planejados)
- Autenticação/tokens (o caminho multipart reusa o mecanismo existente)
- Nenhuma dependência nova no frontend

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária |
|-----------------------------------|------------|-----------------|-----------------|
| `/docs/01-PRD.md`                 | Não (conteúdo) | — | RF-21/US-29/RNs já cobrem a UI (escritos no CR-046 para a F07 completa); apenas conferir refs |
| `/docs/02-ARCHITECTURE.md`        | Sim | Estrutura de pastas (frontend) | Adicionar página/hooks/componentes novos |
| `/docs/03-SPEC.md` + specs/10     | Sim | Seção Frontend da spec F07 | Detalhar componentes implementados; registrar CR-047 no índice |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim | Visão geral | Registrar CR-047 |
| `/docs/05-DEPLOY-GUIDE.md`        | Não | — | Sem novas variáveis/migrations |
| `CLAUDE.md`                       | Sim | Change Requests, estrutura frontend | Adicionar CR-047, mover CR-042 para INDEX |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                                | Descrição da Mudança |
|-----------|---------------------------------------------------|----------------------|
| Modificar | `frontend/src/types.ts`                           | Tipos de importação (batch, transação, confirm) |
| Modificar | `frontend/src/services/api.ts`                    | `requestMultipart` + funções `uploadImport`, `fetchPendingImports`, `fetchImportBatch`, `confirmImport`, `deleteImportBatch` |
| Criar     | `frontend/src/hooks/useImports.ts`                | Query de pending + mutations (upload/confirm/discard) com invalidação de caches |
| Criar     | `frontend/src/utils/importReview.ts`              | Helpers puros do estado de revisão (agrupamento, decisões default, montagem do payload) |
| Criar     | `frontend/src/pages/ImportView.tsx`               | Página `/import` com o stepper do fluxo |
| Criar     | `frontend/src/components/imports/ImportUpload.tsx`    | Passo de upload (seleção de PDF + validação client-side + estados indisponivel/erro) |
| Criar     | `frontend/src/components/imports/ImportReview.tsx`    | Passo de revisão (grupos, edição inline, seleção) |
| Criar     | `frontend/src/components/imports/ImportResult.tsx`    | Passo de resultado (contadores + ações de navegação) |
| Modificar | `frontend/src/components/ViewSelector.tsx`        | Aba "Importar" |
| Modificar | `frontend/src/App.tsx`                            | Rota `/import` protegida |
| Modificar | `frontend/src/services/api.test.ts`               | Testes do caminho multipart (sem Content-Type, Bearer, refresh-401) |
| Criar     | `frontend/src/utils/importReview.test.ts`         | Testes dos helpers de revisão |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| —    | Nenhuma   | Não                   |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When |
|---------|-------------------------------------|------------|-----------|
| CR-T-01 | Tipos + `requestMultipart` + funções de API | — | Testes do api.ts passam |
| CR-T-02 | Helpers `importReview.ts` + testes  | CR-T-01    | Vitest verde |
| CR-T-03 | Hooks `useImports.ts`               | CR-T-01    | tsc sem erros |
| CR-T-04 | Página `/import` + componentes + rota + aba | CR-T-02, CR-T-03 | Fluxo navegável no browser |
| CR-T-05 | Build TS + lint + Vitest (regressão) | CR-T-04   | Tudo verde |
| CR-T-06 | Validação runtime via Playwright (fluxo completo com lote seedado) | CR-T-05 | Registro no CR |
| CR-T-07 | Code review pré-merge (`/code-review`) | CR-T-06 | Findings tratados |
| CR-T-08 | Atualizar documentação              | CR-T-07    | Docs sincronizados |

---

## 8. Critérios de Aceite

- [ ] Aba "Importar" no ViewSelector navega para `/import` (rota protegida)
- [ ] Upload de PDF exibe estado "processando" e, ao concluir, a tela de revisão com as transações agrupadas por classificação
- [ ] Revisão permite: incluir/excluir transação, editar descrição/valor/data/categoria/subcategoria/método, trocar destino (gasto diário ↔ conciliar planejado ↔ descartar)
- [ ] Transações `ignorar` e `duplicada` aparecem em seções separadas, desmarcadas por padrão, e podem ser resgatadas
- [ ] Confirmação chama `/confirm` com as decisões e exibe o resumo (criados/atualizados/descartadas); caches de gastos diários e visão mensal são invalidados
- [ ] Lote pendente de revisão é oferecido para retomada ao entrar em `/import`
- [ ] Respostas `indisponivel`/`erro` do upload exibem mensagem explicativa sem quebrar a página
- [ ] `requestMultipart` envia Bearer token, NÃO seta Content-Type manualmente e mantém o refresh-401 com retry
- [ ] Testes existentes continuam passando (regressão: Vitest + tsc + eslint)
- [ ] Novos testes cobrem a mudança (api multipart + helpers de revisão)
- [ ] Fluxo afetado exercitado em runtime antes do merge via Playwright — registrar o que foi validado
- [ ] Revisão de código pré-merge executada (complexidade Média) — registrar findings
- [ ] Revisão de segurança executada ou justificada
- [ ] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. Critério pendente de evento posterior (ex: CI verde após push) mantém o CR "Em Implementação" até o follow-up.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral | Probabilidade | Impacto | Mitigação |
|----|--------------------------|---------------|---------|-----------|
| 1  | Upload longo (~90s) frustra o usuário ou sofre timeout do browser | Média | Médio | Estado "processando" com aviso de demora; fetch não tem timeout default no browser |
| 2  | Regressão no client HTTP ao introduzir multipart | Baixa | Alto | Caminho novo separado (`requestMultipart`) sem tocar no `request` JSON existente; testes de ambos |
| 3  | Revisão com muitas transações fica pesada | Baixa | Baixo | Renderização simples por grupos; sem virtualização (YAGNI para volume pessoal) |
| 4  | Dupla submissão do confirm | Média | Médio | Botão desabilitado durante a mutation; backend já responde 409 para lote não pendente |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-047` → `git revert [hash(es)]` → merge em `master` → push
- **Metodo alternativo:** Redeploy do deployment anterior via Railway Dashboard
- **Commits a reverter:** commits da branch `feat/CR-047-importacao-extratos-frontend`

### 10.2 Rollback de Migration

- N/A — sem migration.

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** Não — mudança exclusivamente de UI.

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma.

### 10.5 Verificacao Pos-Rollback

- [ ] Aplicacao acessivel e funcional
- [ ] Abas existentes do ViewSelector funcionando
- [ ] CRUD manual de gastos diarios/planejados intacto

---

## Changelog

| Data       | Autor  | Descrição |
|------------|--------|-----------|
| 2026-08-12 | Claude | CR criado (UI da F07; backend no CR-046) |
