# CLAUDE.md — Instruções do Projeto

> **Como usar este template:**
> 1. Copie este arquivo para a raiz do seu projeto como `CLAUDE.md`
> 2. Substitua todos os `[placeholders]` pelo contexto real do projeto
> 3. Remova as linhas de instrução (como esta)
> 4. Mantenha este arquivo sempre atualizado conforme o projeto evolui

---

## Identidade do Projeto

- **Nome:** [Nome do Produto]
- **Descrição:** [Descrição resumida do que o sistema faz e para quem]
- **Stack:** [Frontend], [Backend], [Banco de Dados], [Ferramentas principais]
- **Repositório:** [URL do repositório Git]

---

## Fluxo de Desenvolvimento (Spec-Driven Development)

Este projeto segue um fluxo de desenvolvimento baseado em documentação. **Nunca implemente código sem antes consultar os documentos existentes.**

### Fases do Fluxo

| Fase | Documento | Caminho | Quando Usar |
|------|-----------|---------|-------------|
| 0 | Change Request (CR) | `/docs/changes/CR-XXX.md` | Alterações e correções em funcionalidades existentes |
| 1 | PRD | `/docs/01-PRD.md` | Definição inicial ou adição de módulos grandes |
| 2 | Arquitetura | `/docs/02-ARCHITECTURE.md` | Decisões de stack, estrutura e padrões |
| 3 | Spec Técnica | `/docs/03-SPEC.md` | Detalhamento técnico de cada feature |
| 4 | Plano de Implementação | `/docs/04-IMPLEMENTATION-PLAN.md` | Ordem e dependências das tarefas |
| 5 | Implementação | Código-fonte | Construção efetiva |
| 6 | Validação | Checklist "Done When" | Verificar critérios de aceite antes do deploy |
| 7 | Deploy e Release | `/docs/05-DEPLOY-GUIDE.md` | Procedimentos de deploy, rollback e verificação |

### Regra de Ouro

```
Documentação PRIMEIRO → Código DEPOIS
```

- Novas features: PRD → Arquitetura → Spec → Plano → Implementação
- Alterações/Correções: CR → Avaliar impacto → Atualizar docs afetados → Implementar
- Bug fix simples: CR → Implementar → Atualizar testes

### IMPORTANTE: CR é Obrigatório

> **NUNCA implemente uma feature ou alteração significativa sem criar o CR primeiro.**
> Mesmo para mudanças urgentes ou aparentemente simples. Se uma alteração já foi feita
> sem CR, crie um retroativamente antes de prosseguir com qualquer follow-up.

---

## Templates e Prompts

### Templates de Documentos

Ao criar qualquer documento do fluxo, **use obrigatoriamente o template correspondente** como base:

| Documento | Template |
|-----------|----------|
| Change Request | `/docs/templates/00-template-change-request.md` |
| PRD | `/docs/templates/01-template-prd.md` |
| Arquitetura | `/docs/templates/02-template-architecture.md` |
| Spec Técnica | `/docs/templates/03-template-spec.md` |
| Plano de Implementação | `/docs/templates/04-template-implementation-plan.md` |

---

## Regras de Implementação

### Antes de Codar

1. **Leia** `/docs/02-ARCHITECTURE.md` para entender stack e padrões
2. **Leia** `/docs/03-SPEC.md` para entender o que construir
3. **Leia** `/docs/04-IMPLEMENTATION-PLAN.md` para entender a ordem
4. **Nunca invente** funcionalidades que não estão na spec
5. **Nunca omita** funcionalidades que estão na spec
6. **Se houver ambiguidade**, pare e pergunte antes de decidir
7. **Explore antes de mudar:** Em tarefas que envolvem deploy, migrations, ou dependências, explore o estado atual antes de agir (o que está deployado, schema do banco, dependências instaladas)

### Durante a Implementação

- Siga a estrutura de pastas do `02-ARCHITECTURE.md`
- Siga as convenções de nomenclatura do `02-ARCHITECTURE.md`
- Implemente uma tarefa por vez conforme o `04-IMPLEMENTATION-PLAN.md`
- Escreva testes para cada funcionalidade
- Verifique o checklist "Done When Universal" ao concluir cada tarefa

### Done When Universal

Toda tarefa (CR-T-XX, T-XXX) só é considerada concluída quando:

**Obrigatórios:**
- [ ] Funcionalidade implementada conforme descrito na tarefa
- [ ] App roda localmente sem erros (backend + frontend)
- [ ] Testes existentes continuam passando (regressão)
- [ ] Novos testes cobrem a funcionalidade adicionada/alterada
- [ ] Commit segue Conventional Commits e referencia o ID da tarefa

**Se aplicável:**
- [ ] Migration testada: upgrade + downgrade
- [ ] Endpoints respondem com status codes corretos
- [ ] Documentos afetados atualizados (Spec, Architecture, CLAUDE.md)
- [ ] Sem erros/warnings no console do browser (frontend)

### Commits

- Formato: Conventional Commits
- Nova feature: `feat: implement T-XXX - [descrição]`
- Correção: `fix: CR-XXX - [descrição]`
- Documentação: `docs: update [documento] for CR-XXX`
- Refactoring: `refactor: [descrição]`
- Testes: `test: add tests for T-XXX`

### Push e Deploy

- Antes de push, verifique se o build passa sem erros de tipo/lint
- Commits devem referenciar o CR relevante (ex: `feat: CR-004 - descricao`)
- Após implementação, atualize TODOS os documentos relacionados antes de push

---

## Regras para Alterações e Correções

Quando eu pedir uma alteração, correção ou nova funcionalidade em algo que já existe:

1. **Crie um Change Request (CR)** usando o template em `/docs/templates/00-template-change-request.md`
2. **Salve** em `/docs/changes/CR-[XXX]-[slug].md` (numere sequencialmente)
3. **Avalie o impacto** nos documentos existentes (PRD, Arquitetura, Spec, Plano)
4. **Atualize os documentos afetados** antes de implementar
5. **Implemente** seguindo as tarefas do CR
6. **Valide** os critérios de aceite do CR + checklist "Done When Universal"
7. **Verifique o build** antes de commitar
8. **Commit e push** referenciando o CR: `feat: CR-XXX - descricao`

**Nunca faça alterações direto no código sem antes documentar o CR.**

---

## Regras para Criação de Documentos

- Ao criar qualquer documento, **leia primeiro o template correspondente** em `/docs/templates/`
- Mantenha versionamento nos documentos (Versão 1.0, 1.1, 2.0...)
- Ao atualizar um documento, adicione entrada no changelog (quando existente)
- Referencie IDs entre documentos (RF-001, RN-001, T-001, CR-001, US-001)
- Use diagramas Mermaid quando aplicável

---

## Estrutura de Pastas do Projeto

> **Preencha conforme a estrutura real do projeto após o setup inicial.**

```
[nome-do-projeto]/
├── docs/
│   ├── 01-PRD.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-SPEC.md
│   ├── 04-IMPLEMENTATION-PLAN.md
│   ├── 05-DEPLOY-GUIDE.md
│   ├── changes/              # Change Requests (CR-XXX)
│   └── templates/            # Templates dos documentos
├── [pasta-backend]/
│   └── ...
├── [pasta-frontend]/
│   └── ...
└── .gitignore
```

---

## Convenções de Código

> **Adapte conforme a stack do projeto.**

| Item              | Padrão        | Exemplo                 |
|-------------------|---------------|-------------------------|
| Arquivos Backend  | [padrão]      | ex: `snake_case.py`     |
| Arquivos Frontend | [padrão]      | ex: `camelCase.ts`      |
| Componentes UI    | [padrão]      | ex: `PascalCase.tsx`    |
| Classes           | [padrão]      | ex: `PascalCase`        |
| Funções           | [padrão]      | ex: `camelCase()`       |
| Tabelas BD        | [padrão]      | ex: `snake_case`        |
| Rotas API         | [padrão]      | ex: `kebab-case`        |

---

## Stack Tecnológica

> **Preencha após definir a stack em `02-ARCHITECTURE.md`.**

| Camada         | Tecnologia | Versão |
|----------------|------------|--------|
| Frontend       | ...        | ...    |
| Build/Dev      | ...        | ...    |
| Estilização    | ...        | ...    |
| State/Fetch    | ...        | ...    |
| Routing        | ...        | ...    |
| Backend        | ...        | ...    |
| ORM            | ...        | ...    |
| Banco de Dados | ...        | ...    |
| Migrations     | ...        | ...    |
| Validação      | ...        | ...    |
| Deploy         | ...        | ...    |

---

## Contexto Atual do Projeto

### Documentos Existentes
- [ ] PRD (`/docs/01-PRD.md`)
- [ ] Arquitetura (`/docs/02-ARCHITECTURE.md`)
- [ ] Spec Técnica (`/docs/03-SPEC.md`)
- [ ] Plano de Implementação (`/docs/04-IMPLEMENTATION-PLAN.md`)
- [ ] Guia de Deploy (`/docs/05-DEPLOY-GUIDE.md`)

### Change Requests Ativos
> *Preencha conforme CRs forem criados.*
- CR-001: [Descrição] ([status])

### Última Tarefa Implementada
> *Mantenha atualizado ao concluir cada tarefa ou CR.*
- [Descrição da última tarefa concluída]

---

## Lembretes Importantes

- **Pergunte antes de assumir.** Se algo não está claro na spec, pergunte.
- **Não corrija o que não foi pedido.** Foque apenas no escopo da tarefa.
- **Testes são obrigatórios.** Toda funcionalidade precisa de cobertura.
- **Um passo de cada vez.** Implemente por grupo/tarefa, não tudo de uma vez.
- **Documente primeiro.** Código sem documentação gera retrabalho.
- **Docs sempre sincronizados.** Ao concluir uma feature ou CR, atualize TODOS os documentos relacionados na mesma sessão (Implementation Plan, PRD, Spec, CR). A tarefa só está completa quando os docs estão atualizados.
- **Não fabrique ferramentas.** Nunca invente ou adivinhe a existência de plugins, comandos CLI ou ferramentas. Se não tiver certeza, verifique a documentação primeiro. Se um comando falhar, reconheça o erro imediatamente.
- **Planeje antes de codar.** Em tarefas complexas (3+ etapas), crie um plano TodoWrite detalhado antes de escrever qualquer código. Inclua: CR, arquivos a modificar, verificação de build, atualizações de docs, commit.

---

## Troubleshooting e Erros Conhecidos

> **Preencha conforme problemas forem encontrados e resolvidos durante o desenvolvimento.**
> Consulte esta seção antes de debugar problemas já resolvidos.

### Dependências

| Problema | Causa | Solução |
|----------|-------|---------|
| [Descrição do problema] | [Causa raiz] | [Como resolver] |

### Banco de Dados / Migrations

| Problema | Causa | Solução |
|----------|-------|---------|
| [Descrição do problema] | [Causa raiz] | [Como resolver] |

### Ambiente de Desenvolvimento

| Problema | Causa | Solução |
|----------|-------|---------|
| [Descrição do problema] | [Causa raiz] | [Como resolver] |
