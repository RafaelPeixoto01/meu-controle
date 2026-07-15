---
name: sdd-pipeline
description: "Pipeline SDD para implementar, corrigir, adicionar ou alterar features. Usar sempre que o usuario pedir para implementar, criar, corrigir, mudar, melhorar, ajustar, adicionar ou refatorar algo no codigo. Detecta contexto automaticamente: projeto novo (PRD → Arquitetura → Spec → Plano → Implementacao) ou alteracao em projeto existente (CR → branch → implementacao → validacao → docs → commit/merge). Use tambem quando o usuario disser 'nova feature', 'bug fix', 'melhoria', 'ajuste', ou pedir qualquer mudanca significativa no sistema."
---

# /sdd-pipeline — Pipeline Completo de Feature (SDD)

Skill para implementacao completa de uma feature ou alteracao, garantindo que todas as etapas do fluxo Spec-Driven Development sejam seguidas. Suporta dois modos: **Novo Projeto** (Fluxo A) e **Change Request** (Fluxo B).

## Instrucoes

Execute **todas** as etapas na ordem indicada. Nao pule nenhuma etapa.

---

### Passo 0. Ler o CLAUDE.md do projeto

Antes de qualquer acao, leia o `CLAUDE.md` na raiz do projeto. Extraia:

- **Onde ficam os documentos:** pasta de docs, templates, diretorio de CRs/changes
- **Convencoes de branch e commit:** o CLAUDE.md e a fonte de verdade para nomenclatura
- **Stack tecnologica:** para adaptar verificacoes de build e seguranca
- **Regras especificas do projeto:** qualquer instrucao que sobreponha o comportamento padrao desta skill

Se o projeto nao tiver `CLAUDE.md`, siga o comportamento padrao descrito nesta skill.

---

### Passo 1. Determinar o Modo de Trabalho

**→ Fluxo A (Novo Projeto)** se: nao ha codebase/documentacao, ou o usuario esta criando um produto/sistema/modulo grande do zero.

**→ Fluxo B (Change Request)** se: o projeto ja tem codigo e documentacao, e o pedido e uma alteracao, correcao, nova feature ou melhoria.

**Se ambiguo → pare e pergunte ao usuario antes de prosseguir.**

---

## Fluxo A — Novo Projeto / Modulo Grande

Execute as fases abaixo em ordem. Para cada fase, leia o template correspondente (conforme CLAUDE.md) antes de escrever.

1. **PRD** — Criar usando template. Preencher todas as secoes: visao geral, objetivos, personas, RFs com prioridade, RNFs, user stories, regras de negocio, fora de escopo. **Validar com o usuario antes de avancar.**
2. **Arquitetura** — Stack tecnologica com ADRs, estrutura de pastas, padroes de codigo, modelo de dados, fluxo da aplicacao.
3. **Spec Tecnica** — Endpoints/API contracts, schemas de banco, fluxos de dados, regras de negocio detalhadas, edge cases.
4. **Plano de Implementacao** — Tarefas agrupadas por fase/grupo, dependencias, criterios "Done When" por tarefa.
5. **Branch** — Criar branch (ex: `feat/mvp` ou `feat/initial-setup`), ajustando conforme CLAUDE.md.

*→ Prossiga para o Passo 2.5 (Exploracao)*

---

## Fluxo B — Alteracao em Projeto Existente (Change Request)

### B1. Change Request (CR) e Branch

1. Liste o diretorio de CRs do projeto para identificar o proximo numero sequencial
2. Verifique se ja existe um CR aberto para este trabalho — se sim, use-o; se nao, crie um novo
3. Para criar o CR:
   - Leia o template de CR do projeto antes de escrever
   - Preencha **todas** as secoes do template: resumo, classificacao, contexto (AS-IS / TO-BE), detalhamento, impacto em docs, impacto no codigo, tarefas, criterios de aceite, riscos e plano de rollback
   - **Adapte o nivel de detalhe a complexidade:** CRs de complexidade Baixa (1-3 tasks, mudancas CSS/UI) podem marcar secoes de rollback de migration e variaveis como "N/A"; CRs de complexidade Media/Alta exigem todas as secoes preenchidas com detalhe
   - Salve no diretorio de CRs do projeto
4. Crie a branch seguindo a convencao do CLAUDE.md (ex: `feat/CR-XXX-slug`, `fix/CR-XXX-slug`, `hotfix/descricao`)

### B2. Planejamento

1. Leia os documentos de referencia do projeto **antes de escrever qualquer codigo** — arquitetura, spec tecnica e plano de implementacao
2. **Avalie o impacto em CADA documento do fluxo SDD.** Para cada um, registre explicitamente se precisa de atualizacao e por que. Inclua esta avaliacao no plano TodoWrite — cada documento que precisar de atualizacao deve ter sua propria tarefa. Esta avaliacao e obrigatoria e deve ser registrada por escrito.
   - **PRD:** se o CR adiciona funcionalidade nova (endpoint, modulo, tela, modelo), o PRD **quase certamente** precisa de atualizacao. Verifique: novo RF, novas user stories, novas regras de negocio, items de "Fora de Escopo" que agora serao implementados, novos termos no glossario, fases do roadmap concluidas.
3. **Se houver ambiguidade ou decisao arquitetural relevante → pare e pergunte antes de prosseguir**
4. Crie um plano `TodoWrite` detalhado com todas as tarefas do CR (implementacao + atualizacao de docs), uma por vez

*→ Prossiga para o Passo 2.5 (Exploracao)*

---

## Passos Comuns (ambos os fluxos)

### Passo 2.5. Exploracao (antes de implementar)

Antes de escrever codigo, explore o estado atual nos pontos relevantes ao trabalho:

- **Migrations:** verificar `alembic current`, schema existente, ultima migration
- **Dependencias:** verificar versoes instaladas (`pip list`, `npm list`)
- **Deploy/Infraestrutura:** verificar o que esta deployado, variaveis de ambiente
- **Arquivos existentes:** ler os arquivos que serao modificados para entender o contexto

Objetivo: evitar implementar sobre premissas incorretas. Se a exploracao revelar discrepancias com o CR ou o plano, atualize-os antes de prosseguir.

Pule esta etapa apenas se o trabalho for exclusivamente documentacao ou mudanca trivial de estilo.

---

### Passo 3. Implementacao

- Implemente as mudancas conforme os documentos de referencia (PRD + Spec para Fluxo A; CR + Spec para Fluxo B)
- Siga as convencoes de codigo definidas no `CLAUDE.md` do projeto
- Escreva testes para cada funcionalidade adicionada ou alterada
- **Commits intermediarios:** ao concluir cada grupo de tarefas, faca commit — nao acumule tudo para o final
- **Para CRs com 5+ tarefas:** ao concluir cada grupo, valide contra o checklist "Done When" do CLAUDE.md antes de prosseguir para o proximo grupo

---

### Passo 4. Revisao de Seguranca

**Executar se o trabalho envolver:** novo endpoint, autenticacao/tokens/sessoes, acesso a dados de outros usuarios (ownership), ou nova dependencia externa.

**Pular com justificativa** se for exclusivamente: mudanca de UI sem endpoints, atualizacao de docs, ou refactoring sem alteracao de contrato.

Execute o checklist de seguranca definido no CLAUDE.md do projeto (secao "Revisao de Seguranca"). Se o projeto nao tiver checklist proprio, verifique no minimo: segredos hardcoded, validacao de inputs, armazenamento seguro de tokens, ownership de dados, queries parametrizadas, CORS/headers, e auditoria de dependencias.

Se nao aplicavel, registre: `"Revisao de seguranca nao aplicavel — [motivo]"`

---

### Passo 5. Verificacao de Build

1. Execute os comandos de build/check do projeto (conforme CLAUDE.md, secao "Push e Deploy")
2. Corrija qualquer erro antes de prosseguir
3. Garanta que os testes existentes continuam passando (regressao)

**Se um commit falhar** (ex: hook de type-check, pre-commit): corrija os erros reportados, re-stage as mudancas, e crie um **novo** commit. Nao use `--amend` em um commit que nao foi criado (o hook bloqueou antes da criacao).

---

### Passo 6. Validacao ("Done When")

Verifique o checklist "Done When" do projeto (definido no CLAUDE.md, secao "Done When Universal"). Se o projeto nao tiver checklist proprio, verifique no minimo: funcionalidade implementada conforme docs, app roda sem erros, testes existentes passando, novos testes adicionados.

#### 6.1 Validacao Runtime (obrigatoria — CR-037)

Todo CR com **superficie de runtime** deve ter o fluxo afetado exercitado em execucao ANTES do merge:

- **Frontend/UI:** suba backend + frontend e exercite o fluxo afetado via Playwright MCP — navegue ate a tela, execute a interacao alterada, e verifique que o console nao tem erros novos (erros pre-existentes documentados nao bloqueiam). Para fluxos autenticados em dev, registre/use um usuario de teste local (a conta demo e de producao e nao tem senha no seed).
- **Backend/endpoint:** chame o endpoint afetado (httpx/Invoke-RestMethod/curl) e verifique status code e payload conforme a spec.
- **Registre no CR o que foi exercitado e o resultado** (na secao de criterios de aceite ou no changelog). Validacao sem registro nao conta.

**Pular apenas com justificativa explicita** se o CR for exclusivamente: documentacao, refactoring sem mudanca de comportamento, ou mudanca sem superficie de runtime (ex: config de CI). Registre: `"Validacao runtime N/A — [motivo]"`.

#### 6.2 Regra de Conclusao (obrigatoria — CR-037)

Um CR so pode receber Status **"Concluido"** quando TODOS os criterios de aceite aplicaveis estiverem marcados `[x]` (ou riscados com justificativa explicita). A entrada de changelog "validacao ✅" so pode ser escrita depois disso. Se um criterio depende de evento posterior (ex: CI verde apos push), deixe o CR como "Em Implementacao" e feche o criterio + status em commit de follow-up apos o evento.

**So prossiga quando todos os itens aplicaveis estiverem concluidos.**

---

### Passo 6.5. Revisao de Codigo pre-merge (CR-040)

**Executar se** o CR tiver complexidade **Media ou Alta** (campo Classificacao do CR).

1. Com a implementacao completa e validada, execute a skill `/code-review` sobre o diff da branch (`git diff master...HEAD`)
2. **Trate cada finding:** corrija no codigo OU justifique por escrito por que nao sera corrigido
3. **Registre o resultado no CR** (secao de criterios ou changelog): quantos findings, quantos corrigidos, quantos justificados
4. Se corrigir algo, re-execute build/testes (Passo 5) antes de prosseguir

**CRs de complexidade Baixa:** pular com registro `"Revisao de codigo N/A — complexidade Baixa"`.

**Fallback:** se a skill `/code-review` nao estiver disponivel no ambiente, faca uma auto-revisao estruturada do diff completo procurando bugs de correcao (logica, edge cases, contratos) e registre da mesma forma.

---

### Passo 7. Atualizacao de Documentacao

> **OBRIGATORIO:** A tarefa NAO esta completa ate que cada documento tenha sido revisado. "Revisar" = abrir o documento, verificar se o conteudo reflete as mudancas, atualizar o que esta desatualizado. Se nao precisa de atualizacao, registre a justificativa.

**Fluxo A:** Revise PRD, Arquitetura, Spec e Plano com ajustes descobertos durante a implementacao. Crie o `CLAUDE.md` se nao existir.

**Fluxo B:** Revise cada documento do fluxo SDD:

| Documento | Verificar |
|-----------|-----------|
| CR | Status → "Concluido" + entrada no changelog |
| Spec Tecnica | Componentes/endpoints/modelos refletem as mudancas? |
| Plano de Implementacao | CR referenciado no header e tabela de visao geral? |
| Arquitetura | Novas decisoes, padroes ou ADRs necessarios? |
| **PRD** | **Ver checklist PRD abaixo** — o PRD e facilmente esquecido; revise com atencao |
| Deploy Guide | Novas variaveis, migrations ou procedimentos? |
| CLAUDE.md | Mudancas estruturais, novos CRs, convencoes alteradas? |

#### Checklist PRD (obrigatorio para CRs que adicionam funcionalidade)

O PRD e o documento mais propenso a ficar desatualizado porque cada secao precisa ser verificada individualmente. Se o CR introduziu nova funcionalidade (novo endpoint, novo modulo, nova tela, novo modelo), verifique **cada item**:

- [ ] **Cabecalho:** versao incrementada, data atualizada, CR adicionado na lista de refs, fase/escopo atualizados
- [ ] **Requisitos Funcionais (RF-XX):** novo modulo/RF adicionado com detalhamento? Se sim, incluir na tabela e criar bloco de detalhamento
- [ ] **User Stories (US-XX):** novas user stories com criterios de aceite para a funcionalidade adicionada?
- [ ] **Regras de Negocio (RN-XXX):** novas regras de negocio que governam o comportamento da feature?
- [ ] **Fora de Escopo:** algum item que estava "fora de escopo" agora foi implementado? Se sim, riscar com ~~strikethrough~~ e anotar o CR
- [ ] **Glossario:** novos termos introduzidos pela feature que precisam de definicao?
- [ ] **Roadmap futuro:** alguma fase futura foi implementada? Se sim, marcar como concluida
- [ ] **Dependencias:** nova dependencia externa (API, biblioteca, servico)?
- [ ] **Historico de versoes:** nova entrada no rodape do documento

Se o CR for apenas fix de UI, refactoring interno ou correcao de bug sem nova funcionalidade, registre: `"PRD nao requer atualizacao — [motivo]"`

**NAO avance para o Passo 8 ate que todos estejam revisados e atualizados.**

---

### Passo 8. Commit, Merge e Push

1. Garanta que todos os commits intermediarios ja foram feitos (Passo 3)
2. Verifique o `git status` — confirme que nao ha arquivos sensiveis staged (`.env`, credentials, secrets)
3. Faca o commit final com mensagem seguindo a convencao do CLAUDE.md (secao "Commits")
4. Faca o merge na branch principal conforme a convencao do projeto, delete a branch e faca push
5. Forneca um resumo: arquivos criados/modificados, testes adicionados, documentos atualizados, referencia ao PRD ou CR
