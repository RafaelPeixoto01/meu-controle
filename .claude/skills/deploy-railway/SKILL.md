---
name: deploy-railway
description: "Deploy para Railway via push para branch principal. Usar quando o usuario pedir para fazer deploy, push para producao, subir para Railway, go live, publicar, ou deploy to production. Detecta automaticamente o tipo de projeto, comandos de build/test, e ferramenta de migration a partir do CLAUDE.md e estrutura do repositorio. Funciona com qualquer stack (Node, Python, Go, Rust, etc.)."
disable-model-invocation: true
---

# /deploy-railway — Deploy para Railway (Producao)

Skill generica para deploy de qualquer projeto no Railway via `git push`. Adapta-se automaticamente ao projeto lendo o CLAUDE.md e detectando a stack.

## Instrucoes

Execute **todas** as etapas na ordem indicada. Nao pule nenhuma etapa. Se qualquer validacao falhar, **pare e corrija antes de prosseguir.**

---

### Passo 0. Ler Contexto do Projeto

Antes de qualquer acao, colete informacoes sobre o projeto:

**0.1. Ler CLAUDE.md** (se existir na raiz do projeto). Extraia:

| Informacao | O que procurar |
|------------|----------------|
| Branch principal | `master`, `main`, ou outra |
| Convencao de branches | Nomenclatura de feature/fix branches |
| Convencao de commits | Conventional Commits, outro padrao |
| Comandos de build | `npm run build`, `cargo build`, etc. |
| Comandos de test | `pytest`, `npm test`, `go test`, etc. |
| Comandos de type-check | `tsc --noEmit`, `mypy`, etc. |
| Ferramenta de migration | Alembic, Prisma, Knex, Django, etc. |
| Deploy guide | Caminho do documento de deploy (se houver) |
| Regras de push/deploy | Checklist pre-deploy, verificacoes obrigatorias |

**0.2. Se nao houver CLAUDE.md**, detecte automaticamente:

| Arquivo/Diretorio | Indica |
|--------------------|--------|
| `package.json` | Node.js — extrair scripts `build`, `test`, `lint`, `typecheck` |
| `tsconfig.json` | TypeScript — `npx tsc --noEmit` como type-check |
| `requirements.txt` / `pyproject.toml` | Python — `pytest` como test runner |
| `alembic.ini` | Alembic migrations |
| `prisma/` | Prisma migrations |
| `Cargo.toml` | Rust — `cargo build`, `cargo test` |
| `go.mod` | Go — `go build ./...`, `go test ./...` |
| `Dockerfile` | Container build (Railway usa para deploy) |
| `railway.toml` / `nixpacks.toml` | Config especifica do Railway |

**0.3. Se existir deploy guide** (detectado no CLAUDE.md), leia-o para extrair checklists e procedimentos especificos do projeto.

**0.4. Registre as variaveis detectadas:**

```
BRANCH_PRINCIPAL = [master|main|...]
CMD_BUILD = [comando de build ou "N/A"]
CMD_TEST = [comando de test ou "N/A"]
CMD_TYPECHECK = [comando de type-check ou "N/A"]
MIGRATION_TOOL = [Alembic|Prisma|Knex|Django|"nenhum"]
DEPLOY_GUIDE = [caminho ou "nenhum"]
```

Informe ao usuario o que foi detectado antes de prosseguir.

---

### Passo 1. Detectar Cenario

Execute os comandos abaixo e classifique o cenario:

| Verificacao | Comando | Resultado |
|-------------|---------|-----------|
| Branch atual | `git branch --show-current` | Se `BRANCH_PRINCIPAL` → **Cenario B**; senao → **Cenario A** |
| Mudancas pendentes | `git status --porcelain` | Se nao vazio → **PARE:** commit ou stash antes de prosseguir |
| Commits nao pushados (Cenario B) | `git log origin/{BRANCH_PRINCIPAL}..HEAD --oneline` | Se vazio → nada a fazer, informe o usuario |
| Nova migration (Cenario A) | `git diff origin/{BRANCH_PRINCIPAL}..HEAD --name-only` e procurar arquivos de migration | Se detectada → ativar flag **MIGRATION** |
| Nova migration (Cenario B) | Verificar arquivos de migration nos commits nao pushados | Se detectada → ativar flag **MIGRATION** |

**Cenarios:**

- **Cenario A:** Em branch de feature/fix — precisa merge em `BRANCH_PRINCIPAL` antes do push
- **Cenario B:** Ja em `BRANCH_PRINCIPAL` — apenas push

Informe: "Detectei **Cenario [A/B]**. Branch: `[nome]`. Migration: **[Sim/Nao]**. Confirma prosseguir?"

Se **MIGRATION** detectada, pergunte: "A migration e destrutiva (apaga dados, remove colunas, altera tipos)?" Se sim → ativar flag **DESTRUCTIVE**.

---

### Passo 2. Pre-Deploy Checklist

Execute os comandos detectados no Passo 0. **Se QUALQUER check falhar → PARE e corrija.**

| Check | Comando | Obrigatorio |
|-------|---------|-------------|
| Build | `{CMD_BUILD}` | Sim (se detectado) |
| Testes | `{CMD_TEST}` | Sim (se detectado) |
| Type-check | `{CMD_TYPECHECK}` | Sim (se detectado) |
| Secrets no historico | `git log origin/{BRANCH_PRINCIPAL}..HEAD -p -- '*.env' '*.key' 'credentials*'` | Sim |
| Checklist do deploy guide | Itens extraidos no Passo 0.3 | Sim (se existir) |

---

### Passo 2.1. Validacao de Migration (se flag MIGRATION)

> Pule esta secao se nao houver nova migration.

Execute os comandos de validacao da ferramenta detectada:

| Ferramenta | Validar apply | Validar rollback |
|------------|---------------|------------------|
| Alembic | `alembic upgrade head` | `alembic downgrade -1` e depois `alembic upgrade head` |
| Prisma | `npx prisma migrate deploy` | `npx prisma migrate reset --skip-seed` (apenas em dev) |
| Django | `python manage.py migrate` | `python manage.py migrate <app> <migration_anterior>` |
| Knex | `npx knex migrate:latest` | `npx knex migrate:rollback` |
| Outra | Adaptar ao equivalente | Adaptar ao equivalente |

Se a validacao falhar → **PARE e corrija a migration antes de prosseguir.**

---

### Passo 2.2. Backup de Banco (se flag DESTRUCTIVE)

> Pule esta secao se a migration nao for destrutiva.

**OBRIGATORIO antes de prosseguir com migration destrutiva.**

```bash
railway run pg_dump -Fc > backup_$(date +%Y%m%d_%H%M%S).dump
```

Se o banco nao for PostgreSQL, adapte o comando ao SGBD do projeto (MySQL: `mysqldump`, SQLite: `cp`).

Confirme com o usuario que o backup foi realizado antes de avancar.

---

### Passo 3. Deploy

#### Cenario A (branch de feature/fix)

```bash
git checkout {BRANCH_PRINCIPAL}
git pull origin {BRANCH_PRINCIPAL}
git merge {BRANCH_FEATURE} --no-ff
git branch -d {BRANCH_FEATURE}
git push origin {BRANCH_PRINCIPAL}
```

Adapte a convencao de merge conforme o CLAUDE.md (ex: `--no-ff`, squash, rebase).

#### Cenario B (ja em branch principal)

```bash
git pull origin {BRANCH_PRINCIPAL} --rebase
git push origin {BRANCH_PRINCIPAL}
```

**Railway detecta o push automaticamente e inicia o build.**

---

### Passo 4. Verificacao Pos-Deploy

#### 4.1. Diagnostico

```bash
railway logs                    # Logs do container
railway run {CMD_MIGRATION_STATUS}  # Ex: alembic current, prisma migrate status
```

#### 4.2. Checklist funcional

Se o deploy guide do projeto definir um checklist de verificacao, use-o. Caso contrario, use o checklist generico:

- [ ] Aplicacao carrega sem erros
- [ ] Funcionalidades principais funcionam (CRUD, autenticacao, navegacao)
- [ ] Nenhum erro critico nos logs (`railway logs`)
- [ ] Migration aplicada corretamente (se aplicavel)

Informe o resultado ao usuario.

---

### Passo 5. Rollback (se necessario)

Se algo deu errado apos o deploy, use a opcao mais adequada:

| Situacao | Opcao | Acao |
|----------|-------|------|
| Codigo quebrou (sem migration) | Redeploy anterior | Railway Dashboard → Deployments → clicar "Redeploy" no deploy anterior |
| Codigo quebrou (permanente) | Git revert | `git revert <hash> && git push origin {BRANCH_PRINCIPAL}` |
| Migration precisa reverter | Rollback migration | `railway run {CMD_MIGRATION_ROLLBACK}` + redeploy codigo anterior |
| Variavel de ambiente errada | Restaurar variavel | Railway Dashboard → Variables → reverter valor |
| Dados perdidos (migration destrutiva) | Restaurar backup | `railway run pg_restore --clean --if-exists -d $DATABASE_URL backup_YYYYMMDD.dump` |

Se o projeto tiver deploy guide com procedimentos de rollback mais detalhados, siga-os em vez desta tabela.
