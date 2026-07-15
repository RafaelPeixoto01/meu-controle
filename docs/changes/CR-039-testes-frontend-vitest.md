# Change Request — CR-039: Testes de Frontend com Vitest

**Versão:** 1.0
**Data:** 2026-07-09
**Status:** Em Implementação
**Autor:** Claude (P2-B do Plano de Melhorias Fable, aprovado por Rafael)
**Prioridade:** Média

---

## 1. Resumo da Mudança

Introduzir testes unitários no frontend com **Vitest**: cobertura da lógica pura de `utils/date.ts` e `utils/format.ts` e do cliente HTTP `services/api.ts` (header de autenticação, interceptor 401 com refresh/retry, tratamento de erros). Novo passo `npm test` no job frontend do CI. Até aqui, "Testes são obrigatórios" só se aplicava ao backend — o frontend tinha zero testes.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Nova Feature (infraestrutura de testes) |
| Origem           | Análise do fluxo SDD 2026-07-08 (item P2-B) |
| Urgência         | Próxima sprint            |
| Complexidade     | Média                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O frontend não tem framework de testes nem nenhum teste. A lógica de `utils/` (datas, formatação BRL) e o cliente HTTP com interceptor 401 (CR-002) só são verificados indiretamente por tsc/eslint e pela validação runtime manual.

### Problema ou Necessidade
Regressões em lógica pura do frontend (formatação, viradas de ano, refresh de token) não são detectadas pelo CI. O interceptor 401 é código crítico de sessão que nunca foi testado isoladamente.

### Situação Desejada (TO-BE)
Vitest configurado (`environment: jsdom`), testes co-localizados (`src/**/*.test.ts`), `npm test` no CI. Cobertura inicial: `utils/date.ts`, `utils/format.ts`, `services/api.ts`.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|----------------|----------------|
| 1  | Framework de testes FE | Inexistente | Vitest + jsdom (devDependencies) |
| 2  | Testes | 0 | `date.test.ts`, `format.test.ts`, `api.test.ts` |
| 3  | CI (job frontend) | npm ci → tsc → eslint | + `npm test` (vitest run) |
| 4  | Scripts npm | dev/build/lint/preview | + `"test": "vitest run"` |

### 4.2 O que NÃO muda

- Nenhum código de produto (`utils/`, `services/` não são alterados — apenas testados)
- Hook de commit (continua tsc+eslint; testes rodam no CI para não lentificar commits)
- Testes de backend (pytest) e demais jobs do CI

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | — (infra de testes, sem produto) | — |
| `/docs/02-ARCHITECTURE.md`        | Sim        | Stack | Adicionar Vitest |
| `/docs/03-SPEC.md`                | Não        | — (índice; specs de features inalteradas) | — |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — | — |
| `/docs/05-DEPLOY-GUIDE.md`        | Sim        | §9.1 (tabela do CI) | Adicionar passo vitest |
| `CLAUDE.md`                       | Sim        | Comandos, Stack, Estrutura, CRs (rotação p/ INDEX.md) | Atualizar |
| `/docs/Plano-de-melhorias-Fable.md` | Sim      | P2-B | Marcar Concluído |
| `/docs/Plano-de-evolucao.md`      | Sim        | Novo P2-3 | Registrar concluído (v1.3) |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho | Descrição |
|-----------|---------|-----------|
| Criar     | `frontend/vitest.config.ts` | Config: environment jsdom, include src/**/*.test.ts |
| Criar     | `frontend/src/utils/date.test.ts` | Meses, labels, viradas de ano (prev/next) |
| Criar     | `frontend/src/utils/format.test.ts` | BRL (espaço não-quebrável do Intl), parcela, datas |
| Criar     | `frontend/src/services/api.test.ts` | Auth header, 401→refresh→retry, refresh falho, erros, 204 |
| Modificar | `frontend/package.json` | devDeps (vitest, jsdom) + script test |
| Modificar | `.github/workflows/ci.yml` | Passo "Unit tests" no job frontend |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Instalar vitest+jsdom, criar config e script | — | `npm test` executa |
| CR-T-02 | Testes utils/date.ts e utils/format.ts | CR-T-01 | Testes verdes cobrindo casos de borda |
| CR-T-03 | Testes services/api.ts (fetch mockado) | CR-T-01 | Auth header, fluxo 401 e erros cobertos |
| CR-T-04 | Passo no CI + docs                  | CR-T-01..03| CI verde com vitest incluído       |

---

## 8. Critérios de Aceite

- [ ] `npm test` (vitest run) passa localmente com os 3 arquivos de teste
- [ ] Testes cobrem: viradas de ano (prev/next), formatBRL/parcela/datas, auth header, 401→refresh→retry com token novo, refresh falho (token removido + erro), erro com detail, resposta 204
- [ ] `npx tsc --noEmit` e `npm run lint` continuam passando (testes incluídos no lint)
- [ ] CI executa vitest no job frontend e fica verde
- [ ] Testes existentes continuam passando (regressão — pytest backend)
- [ ] Fluxo afetado exercitado em runtime — **N/A: CR adiciona apenas testes e config de CI; nenhum código de produto alterado, sem superfície de runtime nova (regra CR-037). Os próprios testes exercitam o código.**
- [ ] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** Status "Concluído" só com todos os critérios `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | `toLocaleDateString("pt-BR")` variar entre Node local (Windows) e CI (Ubuntu) | Baixa | Baixo | Node 18+ embute full-ICU; asserção usa valor determinístico verificado nos dois ambientes via CI |
| 2  | jsdom não implementar navegação (`window.location.href =`) no teste do 401 | Média | Baixo | Asserções focam em localStorage e erro lançado; navegação não é asserida |
| 3  | Novas devDependencies com vulnerabilidades | Baixa | Médio | `npm audit` na revisão de segurança |

---

## 10. Plano de Rollback

- **Rollback de Código:** `git revert` do commit (remove testes, config e passo do CI)
- **Rollback de Migration:** N/A
- **Impacto em Dados:** N/A
- **Rollback de Variáveis de Ambiente:** N/A

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-09 | Claude | CR criado e implementação iniciada |
