# Change Request — CR-041: Housekeeping — 7 itens menores do Plano de Melhorias

**Versão:** 1.1
**Data:** 2026-07-15
**Status:** Concluído
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

- [x] `pip-audit` instalado via requirements-dev e executado — resultado registrado (§8.2)
- [x] `backend/.env.example` criado apenas com nomes/placeholders (zero valores reais; default de CLAUDE_MODEL conferido no código)
- [x] Console do dev server sem o erro `createRoot()` duplicado — 0 erros em /login, /register e fluxo completo (§8.1)
- [x] Favicon responde 200 (`image/svg+xml`) e sem 404 no console; `npm run build` copia para `dist/` e `serve_spa` serve em produção
- [x] Zero arquivos `.js` em `frontend/src/` (69 deletados)
- [x] `.claude/hooks`, `.claude/skills` e `.claude/settings.json` rastreados no git (scan de segredos limpo)
- [x] `docs/specs/09-analise-ia.md` criado refletindo a implementação real; lacuna removida do índice (SPEC v3.1)
- [x] Suítes existentes passando: vitest 26/26 + pytest 90/90 + tsc + lint (0 erros)
- [x] Fluxo afetado exercitado em runtime — ver §8.1
- [x] Revisão de código pré-merge executada — ver §8.3 (1 finding confirmado, corrigido)
- [x] CI verde após push (run 29446450818, 42s — pip-audit informativo executou e reportou; passo não-bloqueante conforme desenho)
- [x] Documentos afetados foram atualizados

## 8.1 Registro da Validação Runtime (CR-037)

Exercitado via Playwright com backend+frontend locais:
1. `/login` e `/register` carregam com **0 erros de console** (antes: 1 erro `createRoot` por load + 404 de favicon)
2. `favicon.svg`: HTTP 200 `image/svg+xml`
3. **Fluxo completo de auth**: registro de usuário de teste local → auto-login → MonthlyView renderizada (a tela do bug do CR-034) → menu do usuário → logout (exercita `queryClient.clear()` do módulo novo, CR-014) → redirect a `/login`. Console limpo do início ao fim.

## 8.2 Registro do pip-audit

- Execução local **bloqueada por SSL** (`CERTIFICATE_VERIFY_FAILED` contra pypi.org — interceptação de certificado nesta máquina; pip funciona por caminho de trust distinto). Registrado no Troubleshooting do CLAUDE.md.
- Mitigação implementada: **passo informativo no CI** (`python -m pip_audit`, `continue-on-error: true`) — auditoria roda em todo push num ambiente com SSL limpo, sem bloquear deploy.
- **Primeiro resultado (run 29446450818): 16 vulnerabilidades em 5 pacotes.** Relevantes em produção: `python-jose 3.3.0` (PYSEC-2024-232/233 + PYSEC-2025-185; fix 3.4.0 — biblioteca do JWT) e `starlette 0.46.2` (7 advisories; fixes 0.47.2+ — base do FastAPI, bump condicionado à compatibilidade com fastapi). Menores: ecdsa (sem fix publicado), python-dotenv, pytest (dev-only). **Follow-up: CR dedicado de atualização de dependências backend** (análogo ao CR-036), registrado no Plano de Melhorias.

## 8.3 Registro da Revisão de Código (Passo 6.5, CR-040) — primeira execução real

Diff da branch revisado nos 8 ângulos (linha a linha, comportamento removido, cross-file, reuso, simplificação, eficiência, altitude, convenções). **3 candidatos, 2 refutados com evidência, 1 confirmado e corrigido:**
1. ~~Favicon 404 em produção~~ — REFUTADO: `serve_spa` (main.py:94) serve arquivos da raiz do static; `npm run build` confirmou `dist/favicon.svg`.
2. ~~Imports quebrados pela deleção dos .js~~ — REFUTADO: nenhum import usa extensão; tsc/vitest verdes.
3. **CONFIRMADO**: CLAUDE.md afirmava "Não existe .env.example no repositório" — obsoleto a partir deste CR. Corrigido no Passo 7 (CLAUDE.md agora referencia o template).

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
| 2026-07-15 | Claude | Validação ✅ — todos os critérios fechados após CI verde (run 29446450818); pip-audit do CI revelou 16 vulns backend → follow-up registrado |
