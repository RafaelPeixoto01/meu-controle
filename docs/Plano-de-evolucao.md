# Plano de Evolucao — Meu Controle

**Versao:** 1.1
**Data:** 2026-07-08
**Autor:** Rafael

---

## Visao Geral

Este documento organiza as melhorias de processo, infraestrutura e fluxo de desenvolvimento do projeto Meu Controle. Diferente do PRD (que define features do produto), este plano foca em **como desenvolvemos e operamos** o projeto.

Os itens estao organizados por prioridade (P0 a P3), onde P0 representa riscos criticos que precisam ser resolvidos imediatamente.

---

## Priorizacao

| Prioridade | Significado | Criterio |
|------------|-------------|----------|
| P0 | Critico | Risco de perda de dados ou incapacidade de reverter problemas em producao |
| P1 | Importante | Prevencao de bugs em producao, melhora significativa de qualidade |
| P2 | Desejavel | Reduz retrabalho e dor recorrente, custo medio |
| P3 | Futuro | Nice-to-have, depende de escala ou contexto |

---

## P0 — Critico

### P0-1: Guia de Deploy e Release

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Documento | `/docs/05-DEPLOY-GUIDE.md` |
| Descricao | Documentar pipeline completo Railway (build, migration, start), variaveis de ambiente por ambiente, procedimentos de rollback e backup |
| Impacto | Sem este guia, rollback e procedimentos de emergencia dependem de memoria individual |

### P0-2: Aprimorar Plano de Rollback no Template de CR

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Documento | `/docs/templates/00-template-change-request.md` (Secao 10) |
| Descricao | Secao 10 do template era generica (3 linhas). Expandida para 5 sub-secoes: rollback de codigo, migration, impacto em dados, variaveis de ambiente, e verificacao pos-rollback |
| Impacto | CRs futuros nascem com plano de rollback robusto desde o rascunho |

---

## P1 — Importante

### P1-1: Fase de Validacao Explicita no Fluxo

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Descricao | Adicionada Fase 6 "Validacao" ao fluxo em `CLAUDE.md`, entre Implementacao (5) e Deploy (7). Referencia o checklist "Done When Universal" |
| Documento afetado | `CLAUDE.md` (fluxo) |

### P1-2: Done When Universal

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Descricao | Criada sub-secao "Done When Universal" em `CLAUDE.md` com checklist obrigatorio (5 itens) e condicional (4 itens). Passo 6 das regras de CR atualizado para referenciar o checklist |
| Documento afetado | `CLAUDE.md` (regras de implementacao) |

### P1-3: Revisao de Seguranca como Fase do Fluxo SDD

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Descricao | Adicionada Fase 6 "Revisao de Seguranca" ao fluxo SDD em `CLAUDE.md` (entre Implementacao e Validacao) e Step 4 na skill `/sdd-pipeline` (na epoca chamada `/feature`). Inclui checklist OWASP adaptado ao stack do projeto (8 itens). Motivacao: CR-010 identificou vulnerabilidades de forma reativa; agora a revisao e proativa e obrigatoria para CRs com endpoints, auth, CRUD ou novas dependencias. |
| Documentos afetados | `CLAUDE.md`, `.claude/skills/sdd-pipeline/SKILL.md` |

---

### P1-4: ESLint com react-hooks no Frontend (CR-035)

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Descricao | ESLint 10 flat config com preset completo (typescript-eslint recommended + eslint-plugin-react-hooks). `rules-of-hooks: error` previne estaticamente a classe de bug do CR-034 (tela branca por hook apos early return). Integrado ao hook de commit local (`check-frontend.js`: tsc + eslint). Motivacao: analise do fluxo SDD (2026-07-08) mostrou ~1 fix para cada feat no historico. |
| Documentos afetados | `CLAUDE.md`, `docs/changes/CR-035-eslint-ci-github-actions.md` |

### P1-5: CI no GitHub Actions (CR-035)

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Descricao | Workflow `.github/workflows/ci.yml` roda pytest (backend) + tsc/eslint (frontend) em cada push em master e em PRs. Fecha a brecha do hook local (que so roda em commits via Claude Code). Follow-up recomendado: habilitar "Wait for CI" no Railway para transformar o CI em gate de deploy (ver Deploy Guide secao 9.2). |
| Documentos afetados | `docs/05-DEPLOY-GUIDE.md` (secao 9), `CLAUDE.md` |

---

## P2 — Desejavel

### P2-1: Secao de Troubleshooting no CLAUDE.md

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Descricao | Migrar licoes aprendidas da MEMORY.md para o CLAUDE.md (passlib+bcrypt, SQLite ALTER FK, Windows quirks). Garante que qualquer sessao tenha acesso a erros conhecidos |
| Documento afetado | `CLAUDE.md` (Secao "Troubleshooting e Erros Conhecidos") |

### P2-2: Gestao de Dependencias

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Descricao | Definir politica de pinning (exato vs range), auditoria periodica (`pip audit`, `npm audit`), processo de atualizacao |
| Documento afetado | `02-ARCHITECTURE.md` (Secao 10: Gestao de Dependencias) |

---

## P3 — Futuro

### P3-1: ADRs Formais

| Campo | Valor |
|-------|-------|
| Status | Pendente |
| Descricao | Criar pasta `docs/adrs/` com template e processo para registrar decisoes arquiteturais com contexto e alternativas |
| Quando | Proximo CR arquitetural grande |

### P3-2: Design Review para CRs Complexos

| Campo | Valor |
|-------|-------|
| Status | Pendente |
| Descricao | Adicionar fase de revisao de design antes da implementacao para CRs de alta complexidade (como foi o CR-002) |
| Quando | Quando houver mais CRs do porte do CR-002 |

---

## Changelog

| Data | Autor | Descricao |
|------|-------|-----------|
| 2026-02-11 | Rafael | Documento criado (v1.0) com itens P0-P3 |
| 2026-02-11 | Rafael | P2-1 e P2-2 concluidos (Troubleshooting no CLAUDE.md, Gestao de Dependencias no 02-ARCHITECTURE.md) |
| 2026-02-26 | Rafael | P1-3 concluido (Revisao de Seguranca como Fase do Fluxo SDD — CLAUDE.md + skill /feature) |
| 2026-07-08 | Claude | v1.1 — P1-4 e P1-5 adicionados e concluidos (ESLint react-hooks + CI GitHub Actions, CR-035); referencia da skill /feature corrigida para /sdd-pipeline |
