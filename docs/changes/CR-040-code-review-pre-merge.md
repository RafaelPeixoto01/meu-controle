# Change Request — CR-040: Revisão de Código pré-merge para CRs Média/Alta

**Versão:** 1.1
**Data:** 2026-07-15
**Status:** Concluído
**Autor:** Claude (P2-C do Plano de Melhorias Fable, aprovado por Rafael)
**Prioridade:** Média

---

## 1. Resumo da Mudança

Adicionar ao pipeline SDD um passo de **revisão de código antes do merge** para CRs de complexidade **Média ou Alta**: executar a skill `/code-review` sobre o diff da branch, tratar cada finding (corrigir ou justificar por escrito) e registrar o resultado no CR. CRs de complexidade Baixa pulam com registro. Fecha o último item P2 da análise do fluxo SDD.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Mudança de processo (SDD) |
| Origem           | Análise do fluxo SDD 2026-07-08 (item P2-C) |
| Urgência         | Backlog                   |
| Complexidade     | Baixa                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O fluxo não tem revisão de código: o merge `--no-ff` em master é direto após build/validação. As camadas existentes (ESLint, tsc, testes, validação runtime) pegam classes específicas de problema, mas nenhuma faz revisão semântica do diff (lógica incorreta, edge cases, simplificações).

### Problema ou Necessidade
CRs grandes (porte do CR-002, CR-026, CR-033) mergeiam sem nenhum segundo olhar sobre o código. O Plano de Evolução já previa isso como P3-2 (design review); este CR ataca o lado pós-implementação.

### Situação Desejada (TO-BE)
Passo 6.5 no pipeline: CRs Média/Alta rodam `/code-review` no diff da branch antes do merge; findings são corrigidos ou justificados no CR; resultado registrado. Baixa complexidade: skip registrado.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|----------------|----------------|
| 1  | Pipeline (skill) | Validação → Docs → Merge | Validação → **Revisão de Código (6.5, se Média/Alta)** → Docs → Merge |
| 2  | Done When Universal (CLAUDE.md) | Sem item de code review | Item "se aplicável": /code-review executado e findings tratados |
| 3  | Template de CR §8 | Sem critério de review | Critério "se aplicável" com registro do resultado |

### 4.2 O que NÃO muda

- Nenhum código de produto
- CRs de complexidade Baixa (skip com registro — sem overhead)
- Demais passos do pipeline, CI, hook

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | — (processo, sem produto) | — |
| `/docs/02-ARCHITECTURE.md`        | Não        | — | — |
| `/docs/03-SPEC.md`                | Não        | — | — |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — | — |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | — (revisão é pré-merge, não afeta deploy) | — |
| `/docs/templates/00-template-change-request.md` | Sim | §8 | Critério se-aplicável |
| `/docs/Plano-de-melhorias-Fable.md` | Sim      | P2-C | Marcar Concluído |
| `/docs/Plano-de-evolucao.md`      | Sim        | Novo P2-4 | Registrar (v1.4) |
| `CLAUDE.md`                       | Sim        | Done When (se aplicável), CRs (rotação) | Atualizar |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho | Descrição |
|-----------|---------|-----------|
| Modificar | `.claude/skills/sdd-pipeline/SKILL.md` | Novo Passo 6.5 (**local, gitignored** — como CR-035/037) |
| Modificar | `CLAUDE.md` | Done When + rotação da lista de CRs |
| Modificar | `docs/templates/00-template-change-request.md` | §8 |
| Modificar | `docs/Plano-de-melhorias-Fable.md` e `docs/Plano-de-evolucao.md` | Status |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Passo 6.5 na SKILL.md               | —          | Skill instrui /code-review para Média/Alta com registro |
| CR-T-02 | CLAUDE.md + template                | —          | Done When e §8 atualizados         |
| CR-T-03 | Planos atualizados                  | CR-T-01..02| P2-C/P2-4 registrados              |
| CR-T-04 | Verificação de consistência         | CR-T-01..03| Semântica idêntica nos 3 documentos |

---

## 8. Critérios de Aceite

- [x] Skill `/sdd-pipeline` tem Passo 6.5 com: gatilho (complexidade Média/Alta), comando (/code-review no diff da branch), tratamento de findings (corrigir ou justificar), registro no CR, e skip registrado para Baixa
- [x] CLAUDE.md: item de code review no "Se aplicável" do Done When Universal
- [x] Template de CR §8: critério se-aplicável de code review
- [x] Consistência semântica entre skill, CLAUDE.md e template (verificado por grep — mesma regra nos 3 lugares)
- [x] Testes existentes continuam passando (regressão — CI verde, run 29443624511, 36s)
- [x] Fluxo afetado exercitado em runtime — **N/A: mudança exclusivamente de processo/documentação (regra CR-037)**
- [x] Revisão de código deste CR — **N/A pela própria regra: complexidade Baixa (docs-only)**
- [x] Documentos afetados foram atualizados

> **Regra de conclusão (CR-037):** Status "Concluído" só com todos os critérios `[x]` ou riscados com justificativa.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | Overhead em CRs Média/Alta (~minutos por review) | Alta | Baixo | Restrito a Média/Alta; Baixa pula com registro |
| 2  | Findings falso-positivos gerando retrabalho | Média | Baixo | Regra permite justificar por escrito em vez de corrigir |
| 3  | Skill /code-review indisponível no ambiente | Baixa | Baixo | Fallback documentado: auto-revisão estruturada do `git diff master...HEAD` com registro |

---

## 10. Plano de Rollback

- **Rollback de Código:** `git revert` do commit (docs versionados); restaurar Passo 6.5 anterior na SKILL.md local
- **Rollback de Migration / Dados / Env Vars:** N/A

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-15 | Claude | CR criado e implementação iniciada |
| 2026-07-15 | Claude | Validação ✅ — todos os critérios fechados após CI verde (run 29443624511) |
