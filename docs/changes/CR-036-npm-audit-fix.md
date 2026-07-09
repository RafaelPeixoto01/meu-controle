# Change Request — CR-036: npm audit fix — vulnerabilidades de dependências frontend

**Versão:** 1.1
**Data:** 2026-07-08
**Status:** Concluído
**Autor:** Claude (follow-up do CR-035 §8.1, aprovado por Rafael)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Aplicar `npm audit fix` no frontend para corrigir 7 vulnerabilidades conhecidas em dependências, sendo a mais grave um advisory **HIGH de RCE não autenticado no react-router 7.0.0–7.15.0** (GHSA-49rj-9fvp-4h2h), que roda em produção. Todos os bumps são semver-compatíveis (sem `--force`), verificado via `npm audit fix --dry-run`.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Bug Fix (segurança de dependências) |
| Origem           | Revisão de segurança do CR-035 (npm audit) |
| Urgência         | Imediata                  |
| Complexidade     | Baixa                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
`npm audit` reporta 7 vulnerabilidades (5 high, 1 moderate, 1 low):

| Pacote | Versão atual | Severidade | Impacto |
|--------|--------------|------------|---------|
| react-router / react-router-dom | 7.0.0 (range vulnerável ≤7.15.0) | **HIGH — RCE não autenticado** (GHSA-49rj-9fvp-4h2h) + XSS, open redirect, CSRF, DoS | **Produção** |
| vite | 6.4.1 | HIGH — path traversal / arbitrary file read no dev server | Só dev |
| rollup | <4.58.1 | HIGH — arbitrary file write via path traversal | Só build |
| picomatch | 4.0.0–4.0.3 | HIGH — ReDoS / method injection | Só build |
| @babel/core | ≤7.29.0 | — arbitrary file read via sourceMappingURL | Só build |
| postcss | <8.5.10 | MODERATE — XSS via unescaped `</style>` | Só build |

### Problema ou Necessidade
O advisory do react-router afeta código servido em produção. Os demais afetam apenas ambiente de dev/build, mas são correções gratuitas (patch/minor).

### Situação Desejada (TO-BE)
`npm audit` sem vulnerabilidades conhecidas; app funcionando idêntico (bumps são minor/patch dentro dos ranges `^` do package.json).

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|----------------|----------------|
| 1  | Versões instaladas das deps vulneráveis (package-lock.json) | Versões vulneráveis (tabela acima) | Versões corrigidas via `npm audit fix` |

### 4.2 O que NÃO muda

- Nenhum código-fonte do projeto (backend ou frontend)
- Ranges do `package.json` (bumps dentro dos ranges `^` existentes; lock atualizado)
- Nenhum endpoint, modelo, migration ou comportamento funcional esperado

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | — (sem mudança de produto) | — |
| `/docs/02-ARCHITECTURE.md`        | Não        | — (política de deps §10 já cobre; processo seguido) | — |
| `/docs/03-SPEC.md`                | Não        | — | — |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — | — |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | — | — |
| `CLAUDE.md`                       | Sim        | Change Requests / Última Tarefa | Adicionar CR-036 |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo           | Descrição da Mudança               |
|-----------|-------------------------------|-------------------------------------|
| Modificar | `frontend/package-lock.json`  | Versões corrigidas pelo audit fix   |
| Modificar | `frontend/package.json`       | Apenas se o audit fix ajustar ranges (não esperado) |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Rodar `npm audit fix`               | —          | `npm audit` sem vulnerabilidades   |
| CR-T-02 | Verificar build/lint/testes         | CR-T-01    | tsc, eslint, `npm run build` e pytest passando |
| CR-T-03 | Validação runtime (react-router)    | CR-T-02    | App sobe e navegação entre rotas funciona |
| CR-T-04 | Atualizar documentação              | CR-T-03    | CLAUDE.md + CR atualizados         |

---

## 8. Critérios de Aceite

- [x] `npm audit` reporta 0 vulnerabilidades
- [x] `npx tsc --noEmit -p tsconfig.app.json` passa
- [x] `npm run lint` passa (0 erros, 8 warnings pré-existentes do CR-035)
- [x] `npm run build` conclui sem erros (6.31s)
- [x] App sobe localmente e navegação client-side (react-router 7.18.1) funciona — validado via Playwright: /login renderiza, clique em "Criar conta" navega para /register, /forgot-password renderiza, rota protegida /dashboard redireciona para /login
- [x] Testes existentes continuam passando (regressão — 90 testes pytest)
- [x] Documentos afetados foram atualizados

## 8.1 Versões efetivamente alteradas

| Pacote | Antes (lock) | Depois |
|--------|--------------|--------|
| react-router-dom | 7.13.0 | **7.18.1** |
| vite | 6.4.1 | 6.4.3 |
| rollup, picomatch, @babel/core, postcss | versões vulneráveis | corrigidas via audit fix |

Apenas `package-lock.json` mudou — os ranges do `package.json` já cobriam as versões corrigidas.

## 8.2 Observações da validação runtime

1. **Erro pré-existente (NÃO causado por este CR):** o console exibe `createRoot() on a container that has already been passed to createRoot()` em todo load no dev server. Verificado por teste A/B — o erro ocorre identicamente com as dependências antigas (react-router 7.13.0/vite 6.4.1). Causa provável: `main.tsx` exporta `queryClient` e é importado por outros módulos. **Candidato a CR futuro:** mover `queryClient` para módulo próprio.
2. **favicon.ico 404:** pré-existente, cosmético.
3. **pip-audit não instalado:** a política de auditoria (Arquitetura §10.2) referencia `pip audit`, mas a ferramenta não está no ambiente. Candidato a adicionar em `requirements-dev.txt` num CR futuro.

**Nota sobre testes novos:** N/A — mudança é exclusivamente de versões de dependências, sem código de produto novo; a cobertura é a suíte existente + validação runtime.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | react-router 7.0 → 7.15+ (15 minors) introduzir regressão de comportamento de rota | Baixa | Alto | Validação runtime das rotas + tsc/lint/build; rollback = revert do commit |
| 2  | vite 6.4.1 → 6.4.3 quebrar dev server ou build | Baixa | Médio | `npm run build` + subir dev server na validação |

---

## 10. Plano de Rollback

- **Rollback de Código:** `git revert` do commit (restaura `package-lock.json`) + `npm ci`
- **Rollback de Migration:** N/A
- **Impacto em Dados:** N/A — nenhum dado afetado
- **Rollback de Variáveis de Ambiente:** N/A — nenhuma variável alterada

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-08 | Claude | CR criado e implementação iniciada |
| 2026-07-08 | Claude | Implementação concluída — validação ✅ (audit 0 vulns, tsc/lint/build OK, 90 testes, runtime via Playwright; A/B confirmou erro createRoot como pré-existente) |
