# Change Request — CR-041: Housekeeping — 7 itens menores do Plano de Melhorias

**Versão:** 1.0
**Data:** 2026-07-15
**Status:** Em Implementação
**Autor:** Claude (follow-ups do Plano de Melhorias Fable, aprovado por Rafael)
**Prioridade:** Média

---

## 1. Resumo da Mudança

Fechar os 7 follow-ups menores acumulados nos CRs 035–038: (1) spec da F06 ausente; (2) `pip-audit` não instalado; (3) erro `createRoot()` duplicado no console dev; (4) artefatos `.js` compilados em `frontend/src/`; (5) `favicon.ico` 404; (6) `.claude/` não versionado; (7) `.env.example` inexistente no backend.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Refactoring + Dívida técnica (housekeeping) |
| Origem           | Follow-ups registrados nos CRs 035, 036 e 038 |
| Urgência         | Backlog                   |
| Complexidade     | Média (toca código de produto: main.tsx, index.html, .gitignore) |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
1. F06 (Análise IA, CR-032) sem seção no SPEC — índice aponta para o doc do CR, cujos caminhos de arquivo eram estimativas divergentes da implementação real.
2. Política de auditoria (02-ARCHITECTURE §10.2) referencia `pip audit`, ferramenta não instalada.
3. `main.tsx` exporta `queryClient` e é importado por `AuthContext` — o entry point vira dependência de módulo, causando `createRoot()` duplicado no console em todo load do dev server (A/B no CR-036 §8.2 confirmou pré-existente).
4. ~35 arquivos `.js` compilados (artefatos antigos de `tsc` sem `noEmit`) ao lado dos `.tsx` em `src/` — não rastreados, mas confundem buscas e imports.
5. `index.html` sem `<link rel="icon">` → 404 de favicon em todo load.
6. `.gitignore` ignora `.claude/` inteiro — hooks e skills do pipeline existem só nesta máquina.
7. Sem `.env.example` — nomes de env vars documentados apenas no CLAUDE.md.

### Situação Desejada (TO-BE)
Todos os 7 itens resolvidos; console dev sem erros; pipeline (hooks/skills) versionado e portável.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|----------------|----------------|
| 1  | Spec F06 | Lacuna no índice do SPEC | `docs/specs/09-analise-ia.md` refletindo a implementação real |
| 2  | pip-audit | Não instalado | Em `requirements-dev.txt`; resultado da 1ª execução registrado |
| 3  | queryClient | Exportado por `main.tsx` | Módulo próprio `src/queryClient.ts`; main e AuthContext importam dele |
| 4  | Artefatos `.js` | ~35 arquivos em `src/` | Deletados |
| 5  | Favicon | 404 | `public/favicon.svg` + link no `index.html` |
| 6  | `.claude/` | Gitignored inteiro | `hooks/`, `skills/` e `settings.json` versionados; `settings.local.json` ignorado |
| 7  | `.env.example` | Inexistente | `backend/.env.example` com nomes e placeholders (sem valores reais) |

### 4.2 O que NÃO muda

- Comportamento funcional do app (queryClient continua singleton com a mesma config; favicon é cosmético)
- Nenhum endpoint, modelo ou migration
- Conteúdo dos hooks/skills (apenas passam a ser versionados)

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | — (housekeeping, sem produto novo) | — |
| `/docs/02-ARCHITECTURE.md`        | Sim        | Estrutura/env | Nota .claude versionado |
| `/docs/03-SPEC.md`                | Sim        | Índice | F06 sai de "lacuna" para linha da tabela |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — | — |
| `/docs/05-DEPLOY-GUIDE.md`        | Sim        | §2 env vars | Referenciar .env.example |
| `CLAUDE.md`                       | Sim        | Estrutura, env vars, CRs (rotação) | Atualizar |
| Planos (Fable/Evolução)           | Sim        | Follow-ups | Marcar concluídos |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho | Descrição |
|-----------|---------|-----------|
| Criar     | `frontend/src/queryClient.ts` | QueryClient singleton (movido de main.tsx) |
| Modificar | `frontend/src/main.tsx` | Importa queryClient do módulo novo; deixa de exportar |
| Modificar | `frontend/src/contexts/AuthContext.tsx` | Import atualizado |
| Criar     | `frontend/public/favicon.svg` | Favicon SVG |
| Modificar | `frontend/index.html` | `<link rel="icon">` |
| Deletar   | `frontend/src/**/*.js` | Artefatos não rastreados (local) |
| Modificar | `backend/requirements-dev.txt` | + `pip-audit` |
| Criar     | `backend/.env.example` | Nomes de env vars com placeholders |
| Modificar | `.gitignore` | `.claude/` seletivo |
| Criar     | `docs/specs/09-analise-ia.md` | Spec F06 (implementação real) |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | G1 backend: pip-audit + .env.example | —         | pip-audit roda; .env.example sem segredos |
| CR-T-02 | G2 frontend: queryClient, favicon, limpar .js | — | Console dev sem createRoot/favicon 404 |
| CR-T-03 | G3 docs: spec 09-analise-ia + índice | —         | F06 na tabela do índice            |
| CR-T-04 | G4 repo: versionar .claude/         | —          | hooks/skills/settings no git       |
| CR-T-05 | Validação runtime + code review (Média) | CR-T-01..04 | Registrados no CR              |

---

## 8. Critérios de Aceite

- [ ] `pip-audit` instalado via requirements-dev e executado — resultado registrado (§8.2)
- [ ] `backend/.env.example` criado apenas com nomes/placeholders (zero valores reais)
- [ ] Console do dev server sem o erro `createRoot()` duplicado (antes: presente em todo load)
- [ ] Favicon responde 200 e aparece na aba (antes: 404)
- [ ] Zero arquivos `.js` em `frontend/src/`
- [ ] `.claude/hooks`, `.claude/skills` e `.claude/settings.json` rastreados no git
- [ ] `docs/specs/09-analise-ia.md` criado refletindo a implementação real; lacuna removida do índice
- [ ] Suítes existentes passando: vitest (26) + pytest (90) + tsc + lint
- [ ] Fluxo afetado exercitado em runtime — login page + navegação com console limpo (registrar no §8.1)
- [ ] Revisão de código pré-merge (/code-review) executada — complexidade Média (registrar findings no §8.3)
- [ ] CI verde após push
- [ ] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** Status "Concluído" só com todos os critérios `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | Mover queryClient quebrar HMR/cache isolation (CR-014 usa queryClient.clear no logout) | Baixa | Alto | Mesmo singleton, só muda o módulo; validação runtime do login + testes |
| 2  | .env.example vazar valor real por descuido | Baixa | Alto | Revisão de segurança: diff inspecionado; apenas placeholders |
| 3  | Versionar .claude/ expor algo sensível de settings.json | Baixa | Médio | settings.json contém só o hook PreToolUse (inspecionado); settings.local.json continua ignorado |

---

## 10. Plano de Rollback

- **Rollback de Código:** `git revert` do(s) commit(s); artefatos .js deletados não são recuperáveis nem necessários (regeneráveis por build antigo, não usados)
- **Rollback de Migration / Dados / Env Vars:** N/A

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-15 | Claude | CR criado e implementação iniciada |
