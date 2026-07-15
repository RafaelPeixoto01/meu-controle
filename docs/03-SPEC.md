# Especificacao Tecnica — Meu Controle (Índice)

**Versao:** 3.1
**Data:** 2026-07-15
**PRD Ref:** 01-PRD v2.3
**Arquitetura Ref:** 02-ARCHITECTURE v2.9
**CR Ref:** CR-002, CR-003, CR-005, CR-007, CR-010, CR-011, CR-012, CR-016, CR-019, CR-021, CR-026, CR-033, CR-038

> **CR-038:** este documento virou um **índice**. O conteúdo técnico completo vive em `docs/specs/`, dividido por feature — extração mecânica do monólito original (4.449 linhas, v2.9), sem alteração de conteúdo.
>
> **Como usar:** leia este índice e **apenas a(s) spec(s) da(s) feature(s) afetada(s)** pelo seu CR. Não é necessário carregar todas as specs.

---

## Specs por Feature

| Arquivo | Conteúdo | RFs / CRs |
|---------|----------|-----------|
| [specs/01-core-visao-mensal.md](specs/01-core-visao-mensal.md) | Resumo, escopo, contratos da API (visão geral), infraestrutura, CRUD de despesas/receitas, visão mensal e totalizadores, gestão de status, transição de mês, duplicar, gastos diários | RF-01..RF-07, RF-13 (CR-005) |
| [specs/02-ui-componentes.md](specs/02-ui-componentes.md) | Wireframe, design system, componentes (MonthNavigator, StatusBadge, modais, tabelas, MonthlyView, ProtectedRoute, UserMenu) | CR-003, CR-002 |
| [specs/03-autenticacao-multiusuario.md](specs/03-autenticacao-multiusuario.md) | Auth backend (JWT, Google OAuth, refresh, recuperação de senha), perfil de usuário, frontend auth, migration 002 | RF-08..RF-12 (CR-002) |
| [specs/04-fluxos-bordas-testes.md](specs/04-fluxos-bordas-testes.md) | Fluxos críticos (carregamento, status, criação, registro, logins, refresh, recuperação), casos de borda, plano de testes, checklists de implementação | Transversal |
| [specs/05-dashboard.md](specs/05-dashboard.md) | Endpoint /api/dashboard, schemas, regras de negócio, componentes | F02 (CR-019) |
| [specs/06-projecao-parcelas.md](specs/06-projecao-parcelas.md) | Endpoint de projeção, schemas, regras de datas reais de vencimento, componentes | F03 (CR-021, CR-022..024, CR-028) |
| [specs/07-score-saude.md](specs/07-score-saude.md) | Endpoints de score, cálculo determinístico (D1–D4), cenário conservador, ações, persistência | F04 (CR-026) |
| [specs/08-alertas.md](specs/08-alertas.md) | Motor de alertas on-demand, 8 tipos (A1–A8), ciclo de vida, endpoints, configurações | F05 (CR-033) |
| [specs/09-analise-ia.md](specs/09-analise-ia.md) | Endpoint /api/analysis, arquitetura real (ai_analysis.py), regras (mês fechado, cache mensal, mesclagem F04, graceful degradation), env vars | F06 (CR-032; criada no CR-041) |

---

## Regras para Novas Specs

- Nova feature → novo arquivo `docs/specs/NN-slug.md` + linha na tabela acima (não apensar conteúdo neste índice)
- Alteração em feature existente → editar o arquivo da feature e registrar o CR na coluna "RFs / CRs"

---

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-02-08 | Rafael | SPEC monolítico criado (v1.0) e evoluído por CR-002..CR-033 até v2.9 |
| 2026-07-09 | Claude | v3.0 — CR-038: dividido em docs/specs/ por feature; este arquivo vira índice |
| 2026-07-15 | Claude | v3.1 — CR-041: criada specs/09-analise-ia.md (F06); lacuna eliminada |
