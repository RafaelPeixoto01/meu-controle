# Change Request — CR-045: Remover skill local `/sdd-pipeline` (consumir versão global)

**Versão:** 1.0
**Data:** 2026-07-15
**Status:** Concluído
**Autor:** Rafael Peixoto (via Claude)
**Prioridade:** Baixa

---

## 1. Resumo da Mudança

A skill `/sdd-pipeline` foi promovida para o diretório global de skills do usuário (`C:\Users\Rafael\.claude\skills\sdd-pipeline\`), junto com a nova skill `/sdd-bootstrap` que instala o kit SDD em projetos novos. Este CR remove a cópia local `.claude/skills/sdd-pipeline/` do repositório para que o projeto consuma a versão global — eliminando o risco de divergência entre duas cópias do mesmo processo.

---

## 2. Classificação

| Campo            | Valor                       |
|------------------|-----------------------------|
| Tipo             | Refactoring (tooling/processo) |
| Origem           | Dívida técnica (evitar divergência entre cópias) |
| Urgência         | Imediata                    |
| Complexidade     | Baixa                       |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
A skill `/sdd-pipeline` existe em dois lugares: `.claude/skills/sdd-pipeline/` (versionada no repo desde o CR-041) e `C:\Users\Rafael\.claude\skills\sdd-pipeline\` (global, criada em 2026-07-15). A cópia do projeto tem precedência, então melhorias na global não valem aqui e vice-versa.

### Problema ou Necessidade
Duas fontes da verdade para o mesmo processo divergem com o tempo (ex: um CR futuro que melhore o pipeline atualizaria só uma das cópias).

### Situação Desejada (TO-BE)
Só a versão global existe; o projeto a consome como qualquer outro. Melhorias no processo são feitas na global e valem para todos os projetos.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                        | Antes (AS-IS)                          | Depois (TO-BE)                       |
|----|-----------------------------|----------------------------------------|--------------------------------------|
| 1  | Skill `/sdd-pipeline`       | Cópia local versionada tem precedência | Resolvida via `~/.claude/skills/` (global) |
| 2  | CLAUDE.md — estrutura       | `.claude/skills/` lista sdd-pipeline   | Nota de que sdd-pipeline é global    |

### 4.2 O que NÃO muda

- O fluxo SDD em si (conteúdo da skill é idêntico — a global é cópia fiel da local)
- As skills locais `/deploy-railway` e `/seed-demo` (específicas do projeto, permanecem)
- O hook `check-frontend.js` e o `settings.json`
- Referências históricas à skill em CRs antigos e Plano de Evolução (são histórico)
- `docs/generate_manual_pratico.py` (script one-off; descreve instalação local como opção válida)

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas                  | Ação Necessária                     |
|-----------------------------------|------------|----------------------------------|-------------------------------------|
| `/docs/01-PRD.md`                 | Não        | — (processo, não produto)        | —                                   |
| `/docs/02-ARCHITECTURE.md`        | Não        | — (§3 não detalha `.claude/skills`) | —                                |
| `/docs/03-SPEC.md`                | Não        | —                                | —                                   |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — (housekeeping, precedente CR-041) | —                                |
| `/docs/05-DEPLOY-GUIDE.md`        | Não        | —                                | —                                   |
| `CLAUDE.md`                       | Sim        | Estrutura de pastas, Lembretes, Change Requests | Atualizar linha `.claude/skills/`, nota de skill global, adicionar CR-045 (CR-040 sai dos 5 recentes) |
| `docs/changes/INDEX.md`           | Não        | — (CR-040 já constava no INDEX — overlap pré-existente) | —      |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                        | Descrição da Mudança                    |
|-----------|-------------------------------------------|------------------------------------------|
| Remover   | `.claude/skills/sdd-pipeline/SKILL.md`    | Skill passa a ser consumida da global    |
| Modificar | `CLAUDE.md`                               | Estrutura + nota de skill global + CR-045 |
| Criar     | `docs/changes/CR-045-skill-sdd-pipeline-global.md` | Este CR                         |

### 6.2 Banco de Dados

| Ação | Descrição | Migration Necessária? |
|------|-----------|-----------------------|
| —    | Nenhuma   | Não                   |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                          | Depende de | Done When                                        |
|---------|--------------------------------------------------|------------|--------------------------------------------------|
| CR-T-01 | Remover `.claude/skills/sdd-pipeline/` do repo   | —          | Pasta ausente do working tree e do índice git    |
| CR-T-02 | Atualizar CLAUDE.md e INDEX.md                   | CR-T-01    | Docs refletem skill global + CR-045 listado      |
| CR-T-03 | Validar resolução da skill via global            | CR-T-01    | Invocação de `/sdd-pipeline` resolve para `~/.claude/skills/` |

---

## 8. Critérios de Aceite

- [x] `.claude/skills/sdd-pipeline/` removida do repositório (working tree + git)
- [x] `/sdd-pipeline` continua disponível via skill global — validado: a invocação da skill nesta sessão resolveu para `C:\Users\Rafael\.claude\skills\sdd-pipeline` (base directory reportado pelo harness), mesmo com a cópia local ainda presente
- [x] ~~Testes existentes continuam passando (regressão)~~ — sem mudança de código de produto; hook de commit roda tsc+eslint e CI roda pytest+tsc+eslint no push
- [x] ~~Novos testes cobrem a mudança~~ — N/A: remoção de arquivo de tooling, sem superfície testável
- [x] Fluxo afetado exercitado em runtime antes do merge — N/A: sem superfície de runtime da aplicação; validação aplicável é a resolução da skill (critério 2), já exercitada nesta sessão (CR-037)
- [x] Revisão de código pré-merge — N/A: complexidade Baixa (CR-040)
- [x] Revisão de segurança — N/A: sem endpoint, auth, dados de usuário ou dependência nova (remoção de arquivo de tooling)
- [x] CI verde após push em master (run 29466952520)
- [x] Documentos afetados foram atualizados (CLAUDE.md; INDEX.md sem mudança — CR-040 já constava)

> **Regra de conclusão (CR-037):** o Status deste CR só pode ser "Concluído" quando todos os critérios acima estiverem `[x]` ou riscados com justificativa. Critério pendente de evento posterior (ex: CI verde após push) mantém o CR "Em Implementação" até o follow-up.

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                                              | Probabilidade | Impacto | Mitigação                                                                 |
|----|------------------------------------------------------------------------|---------------|---------|---------------------------------------------------------------------------|
| 1  | Skill global apagada/renomeada → projeto fica sem `/sdd-pipeline`     | Baixa         | Médio   | Conteúdo recuperável do histórico git (`git show 9e3bbcf:.claude/skills/sdd-pipeline/SKILL.md`); memória do agente registra a promoção |
| 2  | Outro colaborador clona o repo e não tem a skill global               | Baixa         | Médio   | CLAUDE.md descreve o fluxo completo em prosa; skill é otimização, não requisito. Projeto é single-dev hoje |
| 3  | Evolução futura do pipeline esquecer de que a fonte é global          | Baixa         | Baixo   | Nota explícita no CLAUDE.md (Lembretes) apontando o caminho global        |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-045` → `git revert [hash do merge] -m 1` → merge em `master` → push
- **Metodo alternativo:** restaurar a pasta: `git checkout 9e3bbcf -- .claude/skills/sdd-pipeline/`
- **Commits a reverter:** merge commit do CR-045

### 10.2 Rollback de Migration

- N/A — sem migration.

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** Não — mudança não toca banco nem runtime.

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma

### 10.5 Verificacao Pos-Rollback

- [ ] `/sdd-pipeline` resolve para a cópia local restaurada
- [ ] CI verde

---

## Changelog

| Data       | Autor  | Descrição                                                        |
|------------|--------|------------------------------------------------------------------|
| 2026-07-15 | Claude | CR criado; skill global já promovida na mesma data (pré-requisito) |
| 2026-07-15 | Claude | Implementação: remoção da pasta, CLAUDE.md atualizado (INDEX.md já continha CR-040) |
| 2026-07-15 | Claude | CI verde (run 29466952520) — validação realizada, status: ✅ Concluído |
