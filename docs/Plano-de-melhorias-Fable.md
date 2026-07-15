# Plano de Melhorias Fable — Meu Controle

**Versão:** 1.0
**Data:** 2026-07-09
**Origem:** Análise do fluxo SDD realizada pelo Claude Fable 5 em 2026-07-08
**Documento relacionado:** `/docs/Plano-de-evolucao.md` (P1-4, P1-5 e P1-6 correspondem aos itens P1 deste plano)

---

## Contexto

Análise do fluxo Spec-Driven Development do projeto identificou que a documentação pré-código era exemplar, mas a verificação pós-código era o elo fraco: ~1 commit de fix para cada feat, com 5 CRs de correção (CR-022..024, 028, 034) causados por bugs que só se manifestam em runtime. As melhorias abaixo foram priorizadas em P1 (previnem bugs em produção), P2 (reduzem custo/retrabalho) e P3 (dependem de escala).

---

## P1 — Prevenção de bugs em produção

| Item | Descrição | CR | Status |
|------|-----------|----|--------|
| P1-A | ESLint com preset completo + `eslint-plugin-react-hooks` (`rules-of-hooks: error`) integrado ao hook de commit — previne estaticamente a classe de bug do CR-034 (tela branca) | CR-035 | ✅ Concluído |
| P1-B | CI no GitHub Actions: pytest (backend) + tsc/eslint (frontend) em cada push/PR — fecha a brecha do hook local, que só roda em commits via Claude Code | CR-035 | ✅ Concluído |
| P1-C | Validação runtime obrigatória no Passo 6 do pipeline (Playwright para UI, HTTP para endpoints, com registro no CR) + regra de conclusão: CR só é "Concluído" com todos os checkboxes fechados | CR-037 | ✅ Concluído |
| — | Habilitar "Wait for CI" no Railway — deploy só sai com checks verdes (passo manual) | — | ✅ Concluído (Rafael, 2026-07-08) |

## P2 — Redução de custo e retrabalho

| Item | Descrição | CR | Status |
|------|-----------|----|--------|
| P2-A | Dividir `03-SPEC.md` (4.449 linhas / ~47k tokens) em specs por feature (`docs/specs/`, 8 arquivos) com índice enxuto no mesmo caminho; histórico de CRs do CLAUDE.md movido para `docs/changes/INDEX.md` (mantém os 5 mais recentes) | CR-038 | ✅ Concluído |
| P2-B | Testes de frontend (Vitest) para lógica crítica: `utils/date.ts`, `utils/format.ts`, `services/api.ts` (auth header, interceptor 401) + passo no job frontend do CI | CR-039 | ✅ Concluído |
| P2-C | `/code-review` antes do merge para CRs de complexidade Média/Alta (passo na skill `/sdd-pipeline` + CLAUDE.md) | — | ⬜ Pendente |

## P3 — Dependente de escala

| Item | Descrição | CR | Status |
|------|-----------|----|--------|
| P3-A | Ambiente de staging no Railway (branch `develop` ou preview environments) — vale o custo quando o app tiver usuários além do Rafael | — | ⬜ Pendente |

## Follow-ups descobertos durante a execução

| Item | Descrição | Origem | Status |
|------|-----------|--------|--------|
| Vulnerabilidades npm | `npm audit fix`: react-router-dom 7.13.0→7.18.1 (RCE HIGH) + 6 dev/build | Revisão de segurança do CR-035 | ✅ Concluído (CR-036) |
| Bug latente no hook de commit | `data.cwd` POSIX/subdiretório quebrava o `path.join` e bloqueava commits legítimos — corrigido priorizando `CLAUDE_PROJECT_DIR` | CR-035 | ✅ Concluído (CR-035) |
| `as any` no InstallmentsView | Escondia `className="undefined"` no StatusBadge — corrigido com type guard | Baseline do ESLint (CR-035) | ✅ Concluído (CR-035) |
| Referência obsoleta à skill `/feature` | Plano de Evolução P1-3 apontava para skill renomeada (`/sdd-pipeline`) | Análise SDD | ✅ Concluído (CR-035) |
| Linha `CLAUDE.md` no template de CR | Tabela de impacto (§5) não tinha a linha; cada CR adicionava à mão | Análise SDD | ✅ Concluído (CR-037) |
| Spec da F06 ausente | Análise IA (CR-032) nunca ganhou seção no SPEC — criar `docs/specs/09-analise-ia.md` a partir do CR-032 | CR-038 §8.1 | ⬜ Pendente |
| `pip-audit` não instalado | Política de auditoria (02-ARCHITECTURE §10.2) referencia a ferramenta, que não existe no ambiente — adicionar a `requirements-dev.txt` | CR-036 §8.2 | ⬜ Pendente |
| `createRoot()` duplicado no console (dev) | Pré-existente (A/B confirmou); causa provável: `main.tsx` exporta `queryClient` importado por outros módulos — mover para módulo próprio | CR-036 §8.2 | ⬜ Pendente |
| Artefatos `.js` compilados em `frontend/src/` | Não rastreados no git; ignorados pelo lint, mas podem confundir imports — deletar | Análise SDD | ⬜ Pendente |
| `favicon.ico` 404 | Cosmético | CR-036 §8.2 | ⬜ Pendente |
| Versionar `.claude/` | Hooks, skills e settings são locais desta máquina (gitignored) — avaliar versionar `.claude/hooks/` e `.claude/skills/` | CR-035 §8.2 | ⬜ Pendente |
| `.env.example` no backend | Não existe; nomes das env vars documentados só no CLAUDE.md | Auditoria CLAUDE.md 2026-07-08 | ⬜ Pendente |

---

## Resumo

- **Concluído:** todas as 3 recomendações P1 + Wait for CI + P2-A + P2-B + 5 follow-ups (CR-035 a CR-039)
- **Pendente:** P2-C (/code-review pré-merge), P3-A (staging) + 7 follow-ups menores

## Changelog

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-07-09 | Claude | Documento criado consolidando as melhorias da análise SDD e seus status |
| 2026-07-09 | Claude | P2-B marcado Concluído (CR-039: Vitest, 26 testes, passo no CI) |
