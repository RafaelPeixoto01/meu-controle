# Plano de Melhorias — Insights Claude Code

**Versao:** 1.0
**Data:** 2026-02-13
**Autor:** Rafael
**Fonte:** Report de Insights Claude Code (9 sessoes, 2026-02-01 a 2026-02-11)

---

## Visao Geral

Este documento consolida todas as sugestoes de melhoria identificadas pelo report de Insights do Claude Code. As sugestoes focam em **workflow, automacao e processo de desenvolvimento** — nao em features do produto.

Os itens estao organizados por prioridade (P0 a P3), onde P0 representa melhorias que resolvem friccoes recorrentes e criticas.

---

## Priorizacao

| Prioridade | Significado | Criterio |
|------------|-------------|----------|
| P0 | Critico | Friccoes recorrentes que ja causaram falhas em deploy ou retrabalho |
| P1 | Importante | Melhorias de processo que previnem erros e aumentam autonomia |
| P2 | Desejavel | Otimizacoes de workflow e automacao de tarefas repetitivas |
| P3 | Futuro | Oportunidades avancadas que dependem de maturidade do tooling |

---

## P0 — Critico

### P0-1: Hook de Validacao TypeScript Pre-Commit

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Features do Claude Code — Hooks |
| Descricao | Configurar hook pre-commit que roda `tsc --noEmit` automaticamente antes de cada commit, impedindo que erros de TypeScript (variaveis nao usadas, parametros incorretos) cheguem ao deploy |
| Impacto | Teria prevenido a falha de deploy no Railway causada por parametros TypeScript nao utilizados apos refactoring |
| Documento afetado | `.claude/settings.json` |

**Configuracao sugerida:**
```json
// .claude/settings.json
{
  "hooks": {
    "pre-commit": {
      "command": "npx tsc --noEmit && echo 'TypeScript check passed'",
      "description": "Run TypeScript type check before committing"
    }
  }
}
```

### P0-2: Reforcar Processo de CR como Obrigatorio no CLAUDE.md

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Melhorias no CLAUDE.md |
| Descricao | Adicionar secao explicita no topo do CLAUDE.md reforando que SEMPRE deve-se criar um CR antes de implementar qualquer feature ou alteracao significativa. Nunca pular este passo — mesmo para mudancas urgentes. Se ja foi feito sem CR, criar retroativamente antes de prosseguir |
| Impacto | Claude pulou o processo de CR durante o redesign do frontend (CR-003 criado retroativamente) |
| Documento afetado | `CLAUDE.md` |

**Texto sugerido para adicionar:**
```markdown
## Change Request (CR) Process
Antes de implementar qualquer feature ou alteracao significativa, SEMPRE crie um
Change Request (CR) primeiro. Nunca pule este passo — mesmo para mudancas urgentes
ou aparentemente simples. Se uma alteracao ja foi feita sem CR, crie um
retroativamente antes de prosseguir com qualquer trabalho de follow-up.
```

### P0-3: Verificacao de Build Pre-Push para Deploy

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Melhorias no CLAUDE.md |
| Descricao | Adicionar secao "Git & Deployment Workflow" ao CLAUDE.md exigindo: (1) commits com referencia ao CR, (2) atualizacao de docs relacionados, (3) verificacao de build TypeScript local antes de push para producao |
| Impacto | Previne deploys quebrados por erros de compilacao que poderiam ser detectados localmente |
| Documento afetado | `CLAUDE.md` |

**Texto sugerido para adicionar:**
```markdown
## Git & Deployment Workflow
- Sempre faca commit com mensagens descritivas referenciando o CR relevante (ex: CR-002, CR-003)
- Apos implementacao, atualize TODOS os documentos relacionados (Implementation Plan, PRDs, status trackers)
- Antes de push para producao, verifique se o build TypeScript passa localmente
  (`npm run build` ou equivalente) para capturar variaveis/parametros nao utilizados
```

---

## P1 — Importante

### P1-1: Custom Skill para Pipeline Completo de Feature

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Features do Claude Code — Custom Skills |
| Descricao | Criar skill `/feature` que codifica o pipeline completo: CR -> implementacao -> testes -> documentacao -> commit -> push. Garante que Claude nao pule etapas mesmo que "esqueca" |
| Impacto | Elimina a necessidade do usuario atuar como "process cop" verificando se cada etapa foi seguida |
| Documento afetado | `.claude/skills/feature/SKILL.md` |

**Configuracao sugerida:**
```bash
mkdir -p .claude/skills/feature
```

```markdown
# /feature - Full Feature Implementation

1. Create or locate the relevant Change Request (CR-XXX) document
2. Plan the implementation using TodoWrite
3. Implement the changes across all necessary files
4. Run `npm run build` (or equivalent) to verify no TypeScript errors
5. Update all related documentation: Implementation Plan, PRD, status trackers
6. Commit with message referencing the CR number
7. Push to remote
8. Provide a summary of all changes made
```

### P1-2: Regra de Atualizacao de Documentacao no CLAUDE.md

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Melhorias no CLAUDE.md |
| Descricao | Adicionar regra explicita: sempre que uma feature for implementada ou um CR for concluido, atualizar TODOS os documentos relacionados na mesma sessao. Nao considerar uma tarefa como completa ate que os docs estejam atualizados |
| Impacto | Multiplas sessoes envolveram atualizacoes de documentacao como workflow principal — manter docs sincronizados com codigo e essencial |
| Documento afetado | `CLAUDE.md` |

**Texto sugerido para adicionar:**
```markdown
## Documentation Updates
Sempre que uma feature for implementada ou um CR for concluido, atualize TODOS
os documentos relacionados na mesma sessao: Implementation Plan, PRD, status
trackers, e qualquer documento de CR. Nao considere uma tarefa como completa ate
que os docs estejam atualizados.
```

### P1-3: Regra de Verificacao de Ferramentas no CLAUDE.md

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Melhorias no CLAUDE.md |
| Descricao | Adicionar regra: nunca fabricar ou adivinhar a existencia de ferramentas, plugins ou comandos CLI. Se nao tiver certeza, verificar documentacao ou buscar primeiro. Se um comando falhar, reconhecer o erro imediatamente ao inves de tentar variacoes de comandos incorretos |
| Impacto | Claude fabricou a existencia de um plugin 'frontend-design' e forneceu comandos inexistentes, causando multiplas rodadas de correcao |
| Documento afetado | `CLAUDE.md` |

**Texto sugerido para adicionar:**
```markdown
## Tool & Plugin Verification
Nunca fabrique ou adivinhe a existencia de ferramentas, plugins ou comandos CLI.
Se nao tiver certeza se algo existe, verifique a documentacao ou busque primeiro.
Se um comando falhar, reconheca o erro imediatamente ao inves de tentar variacoes
de comandos incorretos.
```

### P1-4: Iniciar Sessoes Complexas com Plano TodoWrite

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Padroes de Uso Recomendados |
| Descricao | Adotar como padrao: antes de escrever qualquer codigo em sessoes complexas, criar um plano TodoWrite detalhado. Incluir: (1) criacao/atualizacao de CR, (2) todos os arquivos a modificar, (3) etapa de verificacao de build, (4) atualizacoes de documentacao necessarias, (5) commit e push |
| Impacto | Sessoes com alto uso de TodoWrite (98 chamadas) tiveram os melhores resultados (fully_achieved). Sessoes sem plano previo tiveram mais friccoes |

**Prompt sugerido para inicio de sessao:**
```
Antes de escrever qualquer codigo, crie um plano TodoWrite detalhado para esta
tarefa. Inclua: 1) Criacao/atualizacao de CR, 2) todos os arquivos a modificar,
3) etapa de verificacao de build, 4) atualizacoes de documentacao necessarias,
5) commit e push. Mostre o plano antes de comecar.
```

---

## P2 — Desejavel

### P2-1: Codificar Workflow CR-Driven como Checklist

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Padroes de Uso Recomendados |
| Descricao | Transformar o workflow CR -> implementacao -> teste -> documentacao -> commit -> push -> atualizacao de status em um checklist explicito no CLAUDE.md. Os melhores resultados aconteceram quando o pipeline completo foi seguido; friccoes vieram de etapas puladas |
| Impacto | Garante consistencia entre sessoes sem depender de memoria do agente |

**Prompt sugerido:**
```
Antes de iniciar qualquer implementacao, verifique se existe um CR para este
trabalho. Se nao, crie seguindo o template em docs/CRs/. Depois implemente,
atualize toda a documentacao, rode o build TypeScript, faca commit referenciando
o CR, e push.
```

### P2-2: Usar Task Agents para Exploracao Pre-Implementacao

| Campo | Valor |
|-------|-------|
| Status | ✅ Concluido |
| Categoria | Padroes de Uso Recomendados |
| Descricao | Antes de implementar mudancas — especialmente em configs de deploy, migrations de banco, ou instalacao de plugins — usar Task agents para explorar o estado atual: o que esta deployado, quais migrations existem, qual o schema atual do banco, e quais dependencias estao instaladas. Reportar antes de prosseguir |
| Impacto | 4 dos pontos de friccao envolveram abordagens erradas ou informacao fabricada. Exploracao previa reduziria false starts |

**Prompt sugerido:**
```
Antes de fazer qualquer mudanca, use um task agent para explorar o estado atual:
verifique o que esta deployado, quais migrations existem, como e o schema atual
do banco, e quais dependencias estao instaladas. Reporte antes de prosseguir
com a implementacao.
```

### P2-3: Headless Mode para Atualizacoes de Documentacao em Batch

| Campo | Valor |
|-------|-------|
| Status | Pendente |
| Categoria | Features do Claude Code — Headless Mode |
| Descricao | Usar Claude em modo nao-interativo para tarefas repetitivas como atualizacao em batch de documentacao. Pelo menos 2 sessoes foram puramente de atualizacao de docs onde Claude trabalhou autonomamente apos o handoff de contexto |
| Impacto | Permite scriptar atualizacoes de docs como one-liners, sem precisar de sessao interativa |

**Exemplo de uso:**
```bash
claude -p "Leia todos os CRs em docs/changes/. Para qualquer CR marcado como 'Concluido', verifique se o Implementation Plan e o PRD refletem o status de conclusao. Atualize quaisquer inconsistencias. Commit com mensagem 'docs: sync documentation with completed CRs'." --allowedTools "Read,Edit,Write,Bash"
```

---

## P3 — Futuro

### P3-1: Pipeline Autonomo CR-Driven com Auto-Validacao

| Campo | Valor |
|-------|-------|
| Status | Pendente |
| Categoria | On the Horizon — Oportunidades Avancadas |
| Descricao | Workflow autonomo que garante que toda implementacao comeca com criacao de CR, passa por implementacao e testes, e termina com atualizacao de documentacao. Claude auto-valida contra as regras do CLAUDE.md em cada estagio, tornando violacoes de processo impossiveis ao inves de apenas improvaveis |
| Quando | Quando models forem mais confiaveis em seguir processos multi-etapa |

**Prompt sugerido:**
```
Leia CLAUDE.md e nossa documentacao de CRs. Quero implementar [DESCRICAO].
Antes de escrever codigo, voce DEVE: 1) Criar um novo CR seguindo nosso template,
2) Atualizar o Implementation Plan com as novas tarefas do CR, 3) So entao
comecar a implementacao. Apos implementacao, rode todos os testes, atualize
documentacao relevante, faca commit com referencia ao CR, e push. Use TodoWrite
para rastrear cada estagio e NAO pule nenhuma etapa. Se algum teste falhar,
debug e corrija antes de prosseguir. No final, forneca um resumo de cada arquivo
alterado e cada artefato de CR criado.
```

### P3-2: Agentes Paralelos de Validacao Pre-Deploy

| Campo | Valor |
|-------|-------|
| Status | Pendente |
| Categoria | On the Horizon — Oportunidades Avancadas |
| Descricao | Usar Task agents em paralelo antes de qualquer push: (1) TypeScript strict compilation, (2) verificacao de variaveis de ambiente e configs de deploy, (3) suite completa de testes. Nao prosseguir com push ate que todos reportem sucesso |
| Quando | Quando pipeline de deploy se tornar mais complexo |

**Prompt sugerido:**
```
Antes de push desta branch, rode validacao pre-deploy completa usando Task agents
em paralelo:
Task 1: Rode 'npx tsc --noEmit --strict' e corrija TODOS os type errors,
  variaveis e parametros nao utilizados.
Task 2: Leia a config de deploy do Railway e verifique se todas as variaveis de
  ambiente referenciadas no codigo existem e estao corretamente configuradas
  (verifique URLs internas vs externas).
Task 3: Rode a suite completa de testes e garanta 100% de aprovacao.
NAO prossiga com git push ate que todas as 3 tasks reportem sucesso. Se alguma
falhar, corrija e re-rode. Reporte um checklist final mostrando pass/fail de
cada gate.
```

### P3-3: Pipelines de Automacao Multi-Estagio com Checkpointing

| Campo | Valor |
|-------|-------|
| Status | Pendente |
| Categoria | On the Horizon — Oportunidades Avancadas |
| Descricao | Para automacoes complexas (como o pipeline de scraping do YouTube), estruturar como pipelines baseados em checkpoints. Cada estagio salva resultados intermediarios em arquivos para que qualquer sessao possa retomar do ultimo checkpoint. Combinar TodoWrite para tracking de estado e Task para paralelismo |
| Quando | Proxima automacao multi-estagio complexa |

**Prompt sugerido:**
```
Preciso que voce construa e execute um pipeline de automacao resiliente para
[DESCRICAO DA TAREFA MULTI-ESTAGIO]. Estruture assim:
1) Use TodoWrite para definir cada estagio com criterios claros de sucesso
2) Apos cada estagio completar, salve resultados em arquivo checkpoint
   (ex: checkpoint_stage1.json) para retomar se interrompido
3) Use Task para paralelizar estagios independentes
4) Se algum estagio falhar, registre o erro, tente uma abordagem alternativa,
   e so pergunte se esgotou 3 estrategias de retry
Antes de comecar, mostre o plano completo do pipeline com estagios estimados.
Depois execute end-to-end, atualizando todos conforme avanca. Output final
deve ser um report de conclusao com todos os artefatos produzidos.
```

---

## Resumo de Friccoes Identificadas

| Friccao | Causa | Solucao Mapeada |
|---------|-------|-----------------|
| Pular workflows estabelecidos (CR process) | Claude nao seguiu o processo documentado | P0-2, P1-1 |
| Ferramentas/comandos alucinados | Claude fabricou plugins e comandos inexistentes | P1-3 |
| Codigo bugado apos refactoring | Build check nao feito antes de commit/deploy | P0-1, P0-3 |
| Falha de deploy por TypeScript | Parametros nao utilizados passaram despercebidos | P0-1, P3-2 |
| URL interna vs externa no Railway | Nao verificou contexto de deploy antes de agir | P2-2 |

---

## Changelog

| Data | Autor | Descricao |
|------|-------|-----------|
| 2026-02-13 | Rafael | Documento criado (v1.0) — consolidacao de todas as sugestoes do report de Insights Claude Code |
| 2026-02-13 | Rafael | P0-1, P0-2, P0-3 concluidos — hook TypeScript pre-commit + regras CR obrigatorio e Push/Deploy no CLAUDE.md |
| 2026-02-13 | Rafael | P1-1, P1-2, P1-3, P1-4 concluidos — skill /feature + regras docs sync, verificacao de ferramentas, plano TodoWrite no CLAUDE.md |
| 2026-02-13 | Rafael | P2-1, P2-2 concluidos — checklist CR expandido (passos 7-8) + regra de exploracao previa no CLAUDE.md |
