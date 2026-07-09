# Change Request — CR-037: Validação Runtime obrigatória no pipeline SDD

**Versão:** 1.0
**Data:** 2026-07-08
**Status:** Em Implementação
**Autor:** Claude (P1-C da análise do fluxo SDD, aprovado por Rafael)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Institucionalizar a **validação em runtime** como passo obrigatório do pipeline SDD (Passo 6 — Validação): todo CR com superfície de runtime deve ter o fluxo afetado exercitado em execução (Playwright para UI, chamada HTTP para endpoints) antes do merge, com registro do que foi validado. Adicionalmente, **regra dura de conclusão**: nenhum CR pode ter Status "Concluído" com critérios de aceite desmarcados.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Mudança de processo (SDD) |
| Origem           | Análise do fluxo SDD 2026-07-08 (item P1-C) |
| Urgência         | Próxima sprint            |
| Complexidade     | Baixa                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
O checklist "Done When Universal" diz "app roda localmente sem erros", mas nada obriga a exercitar o fluxo afetado. O histórico mostra ~1 fix por feat; os CRs 022–024, 028 e 034 corrigem bugs que só se manifestam em runtime. O CR-034 foi marcado "Concluído" com 3 critérios de aceite desmarcados — incluindo "app não exibe tela branca após login" — e precisou de um segundo commit de correção pós-merge.

### Problema ou Necessidade
ESLint (CR-035) cobre a classe estática e o CI (CR-035) roda os testes, mas bugs de integração/renderização escapam de ambos. A validação runtime existente é informal (o CR-036 a praticou voluntariamente via Playwright).

### Situação Desejada (TO-BE)
Validação runtime como etapa formal do Passo 6 do pipeline, com critério fixo no template de CR, item no Done When Universal, e proibição de concluir CR com checkbox aberto.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item | Antes (AS-IS) | Depois (TO-BE) |
|----|------|----------------|----------------|
| 1  | Passo 6 da skill `/sdd-pipeline` | Checklist genérico "Done When" | + Validação runtime obrigatória (UI via Playwright, endpoint via HTTP) com registro no CR |
| 2  | Status "Concluído" do CR | Possível concluir com checkbox aberto (CR-034) | Só com todos os critérios `[x]` ou riscados com justificativa |
| 3  | Done When Universal (CLAUDE.md) | 5 itens obrigatórios | + item "fluxo afetado exercitado em runtime ou N/A justificado" |
| 4  | Template de CR §8 | Critérios genéricos | + critério fixo de validação runtime |
| 5  | Template de CR §5 | Tabela sem linha CLAUDE.md | + linha CLAUDE.md (hoje cada CR adiciona manualmente) |

### 4.2 O que NÃO muda

- Nenhum código de produto (backend/frontend)
- Estrutura das demais fases do pipeline SDD
- CI, hook de commit e fluxo de branches (CR-035)

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | — (processo, sem mudança de produto) | — |
| `/docs/02-ARCHITECTURE.md`        | Não        | — | — |
| `/docs/03-SPEC.md`                | Não        | — | — |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — | — |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | — (checklist pré-deploy já cobre lint/CI; validação runtime é pré-merge) | — |
| `/docs/templates/00-template-change-request.md` | Sim | §5, §8 | Critério runtime + linha CLAUDE.md |
| `/docs/Plano-de-evolucao.md`      | Sim        | P1-6 novo | Registrar concluído (v1.2) |
| `CLAUDE.md`                       | Sim        | Done When Universal, Lembretes, Change Requests | Atualizar |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo           | Descrição da Mudança               |
|-----------|-------------------------------|-------------------------------------|
| Modificar | `.claude/skills/sdd-pipeline/SKILL.md` | Passo 6 com validação runtime + regra de conclusão (**local, gitignored** — como no CR-035) |
| Modificar | `CLAUDE.md`                   | Done When Universal + Lembretes     |
| Modificar | `docs/templates/00-template-change-request.md` | §5 e §8 |
| Modificar | `docs/Plano-de-evolucao.md`   | P1-6 (v1.2)                         |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                              | Depende de | Done When                          |
|---------|-------------------------------------|------------|------------------------------------|
| CR-T-01 | Atualizar SKILL.md Passo 6          | —          | Skill instrui validação runtime + regra de conclusão |
| CR-T-02 | Atualizar CLAUDE.md                 | —          | Done When e Lembretes atualizados  |
| CR-T-03 | Atualizar template de CR            | —          | §5 com CLAUDE.md, §8 com critério runtime |
| CR-T-04 | Atualizar Plano de Evolução         | CR-T-01..03| P1-6 registrado                    |
| CR-T-05 | Verificação de consistência + teste retroativo | CR-T-01..04 | Docs consistentes; CR-034 seria bloqueado, CR-036 passaria |

---

## 8. Critérios de Aceite

- [x] Skill `/sdd-pipeline` (Passo 6) exige validação runtime com registro no CR e regra de conclusão (novas subseções 6.1 e 6.2)
- [x] CLAUDE.md: Done When Universal contém o item de validação runtime; Lembretes contêm a regra de conclusão
- [x] Template de CR: §8 com critério fixo de runtime + nota da regra de conclusão; §5 com linha CLAUDE.md
- [x] Teste retroativo documentado (ver §8.1)
- [ ] Testes existentes continuam passando (regressão — CI verde) — *pendente do push; CR permanece "Em Implementação" até o follow-up, conforme a própria regra 6.2*
- [x] Fluxo afetado exercitado em runtime — **N/A justificado**: mudança exclusivamente de processo/documentação, sem superfície de runtime
- [x] Documentos afetados foram atualizados

## 8.1 Teste Retroativo (CR-T-05)

| CR | Sob as novas regras | Resultado |
|----|---------------------|-----------|
| CR-034 (e o CR-033 que o originou) | 6.1 exigiria exercitar o fluxo pós-login via Playwright — exatamente onde a tela branca se manifestava; 6.2 impediria o status "Concluído" com 3 checkboxes abertos | **Bloqueado 2×** — o bug não chegaria em produção |
| CR-036 | Runtime exercitado e registrado (§8: rotas públicas + redirect de rota protegida via Playwright); todos os critérios fechados antes do status | **Passaria** — já praticou o padrão |

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | Overhead por CR (subir app + exercitar fluxo, ~3–5 min) | Alta | Baixo | Cláusula de skip justificado para CRs sem superfície de runtime |
| 2  | Validação superficial "pró-forma" (exercitar sem observar) | Média | Médio | Exigência de registrar O QUE foi exercitado e o resultado no CR |

---

## 10. Plano de Rollback

- **Rollback de Código:** `git revert` do commit (docs versionados); restaurar Passo 6 anterior na SKILL.md local
- **Rollback de Migration:** N/A
- **Impacto em Dados:** N/A
- **Rollback de Variáveis de Ambiente:** N/A

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-08 | Claude | CR criado e implementação iniciada |
