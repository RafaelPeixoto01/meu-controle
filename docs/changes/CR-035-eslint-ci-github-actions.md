# Change Request — CR-035: ESLint (react-hooks) + CI no GitHub Actions

**Versão:** 1.0
**Data:** 2026-07-08
**Status:** Em Implementação
**Autor:** Claude (análise do fluxo SDD aprovada por Rafael)
**Prioridade:** Alta

---

## 1. Resumo da Mudança

Adicionar duas camadas de verificação automática ausentes no projeto: (a) **ESLint** no frontend com preset completo (`typescript-eslint` recommended + `eslint-plugin-react-hooks`), integrado ao hook de commit do Claude Code; (b) **CI no GitHub Actions** rodando `pytest` (backend) + `tsc --noEmit` + `eslint` (frontend) em cada push/PR. Corresponde aos itens P1-A e P1-B da análise do fluxo SDD.

---

## 2. Classificação

| Campo            | Valor                     |
|------------------|---------------------------|
| Tipo             | Dívida técnica / Infraestrutura de processo |
| Origem           | Análise do fluxo SDD (2026-07-08) |
| Urgência         | Próxima sprint            |
| Complexidade     | Média                     |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)
- O frontend não tem ESLint — nenhuma regra de lint é aplicada.
- O único gate de qualidade é o hook `.claude/hooks/check-typescript.js` (PreToolUse), que roda `tsc --noEmit` apenas em commits feitos através do Claude Code. Commits manuais no terminal não passam por verificação alguma.
- Os testes do backend (`backend/tests/`, 5 arquivos) só rodam quando executados manualmente — nunca como gate.
- Push em `master` dispara auto-deploy no Railway sem nenhuma verificação automática no caminho.

### Problema ou Necessidade
O histórico do projeto tem ~1 commit de fix para cada feat. O CR-034 (tela branca em produção por violação das Rules of Hooks) é o exemplo crítico: a regra `react-hooks/rules-of-hooks` do ESLint teria bloqueado o bug estaticamente, no commit. Sem CI, uma regressão no backend só é descoberta em produção.

### Situação Desejada (TO-BE)
- ESLint com preset completo roda no hook de commit (junto com `tsc`) e bloqueia commits com erros de lint.
- GitHub Actions roda `pytest` + `tsc` + `eslint` em cada push em `master` e em PRs, servindo de rede de segurança independente de onde o commit nasceu.
- (Passo manual recomendado) Railway configurado com "Wait for CI" para que o deploy aguarde os checks verdes.

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                    | Antes (AS-IS)        | Depois (TO-BE)       |
|----|-------------------------|----------------------|----------------------|
| 1  | Lint no frontend        | Inexistente          | ESLint 9 flat config: `typescript-eslint` recommended + `react-hooks` (rules-of-hooks: error) |
| 2  | Hook de commit          | `check-typescript.js` roda só `tsc` | Renomeado para `check-frontend.js`, roda `tsc` + `eslint` |
| 3  | Verificação contínua    | Inexistente          | `.github/workflows/ci.yml` com jobs backend (pytest) e frontend (tsc + eslint) |
| 4  | Dependências dev backend| pytest não pinado    | `backend/requirements-dev.txt` com `pytest==8.*` |

### 4.2 O que NÃO muda

- Nenhum código de produto (backend ou frontend) muda de comportamento — apenas correções de lint sem efeito funcional, se necessárias na baseline
- Fluxo de deploy no Railway (auto-deploy no push em master permanece; "Wait for CI" é opt-in manual)
- Fluxo de branches e convenções de commit
- Nenhum endpoint, modelo ou migration

---

## 5. Impacto nos Documentos

| Documento                         | Impactado? | Seções Afetadas | Ação Necessária     |
|-----------------------------------|------------|-----------------|---------------------|
| `/docs/01-PRD.md`                 | Não        | — (infra de processo, sem mudança de produto) | — |
| `/docs/02-ARCHITECTURE.md`        | Não*       | §10 Gestão de Dependências revisada — CI reforça a política existente | Revisar; atualizar apenas se houver lacuna |
| `/docs/03-SPEC.md`                | Não        | — (sem endpoints/modelos) | — |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Não        | — (CR de infra, sem tarefas de produto) | — |
| `/docs/05-DEPLOY-GUIDE.md`        | Sim        | Nova seção: CI e "Wait for CI" | Adicionar seção |
| `/docs/Plano-de-evolucao.md`      | Sim        | Novos itens P1-4/P1-5 concluídos; ref. obsoleta à skill `feature` | Atualizar (v1.1) |
| `CLAUDE.md`                       | Sim        | Comandos, stack, estrutura, hook, lista de CRs | Atualizar |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo                        | Descrição da Mudança               |
|-----------|-------------------------------------------|-------------------------------------|
| Criar     | `frontend/eslint.config.js`               | Flat config ESLint 9 (ts recommended + react-hooks) |
| Modificar | `frontend/package.json`                   | devDependencies + script `lint`     |
| Modificar | `frontend/src/**` (pontual)               | Correções de baseline do lint, se houver |
| Renomear  | `.claude/hooks/check-typescript.js` → `check-frontend.js` | Adicionar passo eslint após tsc |
| Modificar | `.claude/settings.json`                   | Caminho e statusMessage do hook     |
| Criar     | `backend/requirements-dev.txt`            | `-r requirements.txt` + `pytest==8.*` |
| Criar     | `.github/workflows/ci.yml`                | CI com jobs backend e frontend      |

### 6.2 Banco de Dados

N/A — nenhuma alteração no banco. Migration não necessária.

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                            | Depende de | Done When                                    |
|---------|---------------------------------------------------|------------|----------------------------------------------|
| CR-T-01 | Instalar deps ESLint + criar `eslint.config.js` + script `lint` | — | `npm run lint` executa com preset completo |
| CR-T-02 | Corrigir violações da baseline (ou rebaixar regra ruidosa para warn com justificativa) | CR-T-01 | `npm run lint` passa sem erros |
| CR-T-03 | Renomear hook para `check-frontend.js` (tsc + eslint) + `settings.json` | CR-T-02 | Commit com erro de lint é bloqueado pelo hook |
| CR-T-04 | Criar `backend/requirements-dev.txt`              | —          | `pip install -r requirements-dev.txt` instala pytest |
| CR-T-05 | Criar `.github/workflows/ci.yml`                  | CR-T-01, CR-T-04 | Workflow válido, 2 jobs paralelos |
| CR-T-06 | Revisão de segurança (npm audit das novas deps)   | CR-T-01    | Sem vulnerabilidades high/critical não mitigadas |
| CR-T-07 | Verificação fim a fim (prova rules-of-hooks, tsc, pytest, CI verde) | CR-T-03, CR-T-05 | Todos os checks verdes local e no GitHub |
| CR-T-08 | Atualizar documentação                            | CR-T-07    | Docs da seção 5 atualizados |

---

## 8. Critérios de Aceite

- [ ] `npm run lint` passa sem erros no código atual
- [ ] Uma violação deliberada de `rules-of-hooks` (hook após early return) faz `npm run lint` falhar E o hook de commit bloquear
- [ ] `tsc --noEmit -p tsconfig.app.json` continua passando
- [ ] `python -m pytest tests/ -v` passa localmente (regressão)
- [ ] CI executa e fica verde no GitHub após o push do merge (jobs backend e frontend)
- [ ] Testes existentes continuam passando (regressão)
- [ ] Documentos afetados foram atualizados

**Nota sobre testes novos:** este CR não adiciona código de produto testável — a "cobertura" da mudança é o próprio CI executando os testes existentes + a prova deliberada de violação de lint (critério 2).

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral           | Probabilidade | Impacto | Mitigação                        |
|----|------------------------------------|---------------|---------|----------------------------------|
| 1  | Baseline com muitas violações de lint, inflando o CR | Média | Médio | Regras ruidosas rebaixadas para `warn` com justificativa registrada aqui; hooks rules sempre `error` |
| 2  | Hook de commit mais lento (tsc + eslint) | Alta | Baixo | ESLint em `src/` apenas; aceitável (~segundos) |
| 3  | CI falhar por diferença de ambiente (Windows dev vs Ubuntu CI) | Baixa | Baixo | Testes usam SQLite in-memory; sem dependência de OS |
| 4  | Correções de baseline alterarem comportamento sem querer | Baixa | Alto | Correções mínimas; `tsc` + pytest + revisão do diff antes do merge |

---

## 10. Plano de Rollback

> Referencia: Procedimentos detalhados em `/docs/05-DEPLOY-GUIDE.md` (secoes 4 e 5).

### 10.1 Rollback de Codigo

- **Metodo:** `git checkout -b hotfix/revert-CR-035` → `git revert [hashes do merge]` → merge em `master` → push
- **Metodo alternativo:** Deletar `.github/workflows/ci.yml` desativa o CI; remover o passo eslint do hook restaura o comportamento anterior
- **Commits a reverter:** listados no changelog ao concluir

### 10.2 Rollback de Migration

N/A — sem migration.

### 10.3 Impacto em Dados

- **Dados serao perdidos no rollback?** Não — mudança não toca banco de dados.
- **Backup necessario antes do deploy?** Não.

### 10.4 Rollback de Variaveis de Ambiente

- **Variaveis novas/alteradas:** Nenhuma em produção (`SECRET_KEY: ci-test-secret` existe apenas dentro do workflow de CI).

### 10.5 Verificacao Pos-Rollback

- [ ] Commit de teste passa pelo hook sem exigir eslint
- [ ] Deploy no Railway ocorre normalmente após push

---

## Changelog

| Data       | Autor  | Descrição                    |
|------------|--------|------------------------------|
| 2026-07-08 | Claude | CR criado e implementação iniciada |
