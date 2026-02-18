# CLAUDE.md — Instruções do Projeto

## Identidade do Projeto

- **Nome:** Meu Controle
- **Descrição:** Rastreador de financas pessoais multi-usuario com autenticacao JWT/Google OAuth2, visao mensal de despesas/receitas, transicao automatica de mes e gestao de status
- **Stack:** React 19 + TypeScript, Vite 6, Tailwind CSS v4, TanStack Query v5, FastAPI, SQLAlchemy 2.0, PostgreSQL/SQLite
- **Repositório:** https://github.com/RafaelPeixoto01/meu-controle.git

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
- [ ] Migration testada: `alembic upgrade head` + `alembic downgrade -1`
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

- Antes de push, verifique se o build TypeScript passa: `cd frontend && npx tsc --noEmit -p tsconfig.app.json`
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
7. **Verifique o build** TypeScript: `cd frontend && npx tsc --noEmit -p tsconfig.app.json`
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

```
Personal Finance/
├── docs/
│   ├── 01-PRD.md
│   ├── 02-ARCHITECTURE.md
│   ├── 03-SPEC.md
│   ├── 04-IMPLEMENTATION-PLAN.md
│   ├── 05-DEPLOY-GUIDE.md           # Guia de deploy, rollback e verificacao
│   ├── Plano-de-evolucao.md          # Roadmap de melhorias de processo/infra
│   ├── changes/              # Change Requests (CR-XXX)
│   └── templates/            # Templates dos documentos
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 001_initial_schema.py
│   │       ├── 002_add_users_and_auth.py  # CR-002
│   │       ├── 003_add_origem_id.py       # RF-06
│       └── 004_add_daily_expenses.py  # CR-005
│   └── app/
│       ├── __init__.py
│       ├── main.py           # Entry point FastAPI + lifespan
│       ├── database.py       # Engine SQLAlchemy + SessionLocal
│       ├── models.py         # ORM: User, Expense, Income, RefreshToken, DailyExpense
│       ├── schemas.py        # Pydantic: request/response + auth + daily expense schemas
│       ├── crud.py           # Acesso a dados + User/RefreshToken/DailyExpense CRUD
│       ├── services.py       # Logica: transicao de mes, auto-status, daily expenses summary
│       ├── categories.py     # CR-005: Categorias e metodos de pagamento (gastos diarios)
│       ├── auth.py           # CR-002: JWT + bcrypt auth module
│       ├── email_service.py  # CR-002: SendGrid email (password reset)
│       └── routers/
│           ├── auth.py       # CR-002: register, login, Google OAuth, refresh, logout, forgot/reset password
│           ├── users.py      # CR-002: GET/PATCH /me, change password
│           ├── expenses.py   # CRUD + duplicate (auth required)
│           ├── incomes.py    # CRUD (auth required)
│           ├── months.py     # GET visao mensal (auth required)
│           └── daily_expenses.py  # CR-005: CRUD gastos diarios + categories (auth required)
├── frontend/
│   ├── package.json
│   ├── vite.config.ts        # Proxy /api -> :8000
│   ├── index.html
│   └── src/
│       ├── main.tsx          # Bootstrap React + QueryClient + BrowserRouter
│       ├── App.tsx           # Shell com AuthProvider + Routes
│       ├── index.css         # Tailwind v4 (@import + @theme)
│       ├── vite-env.d.ts     # Vite client types
│       ├── types.ts          # Tipos + Auth types (CR-002) + DailyExpense types (CR-005)
│       ├── utils/            # format.ts (formatBRL, formatDateFull), date.ts
│       ├── services/
│       │   ├── api.ts        # HTTP client com auth header + 401 interceptor + daily expenses API
│       │   └── authApi.ts    # CR-002: auth API functions
│       ├── contexts/
│       │   └── AuthContext.tsx  # CR-002: auth state management
│       ├── hooks/            # useExpenses, useIncomes, useMonthTransition, useAuth, useDailyExpenses
│       ├── components/       # MonthNavigator, Tables, Forms, Modals, ProtectedRoute, UserMenu, ViewSelector
│       └── pages/            # MonthlyView, DailyExpensesView, Login, Register, ForgotPassword, ResetPassword, Profile
├── CLAUDE.md
└── .gitignore
```

---

## Convenções de Código

| Item              | Padrão        | Exemplo                 |
|-------------------|---------------|-------------------------|
| Arquivos Python   | snake_case    | `services.py`           |
| Arquivos TS/TSX   | camelCase     | `useExpenses.ts`        |
| Componentes React | PascalCase    | `ExpenseTable.tsx`      |
| Classes Python    | PascalCase    | `ExpenseStatus`         |
| Funcoes Python    | snake_case    | `get_expenses_by_month` |
| Funcoes TS        | camelCase     | `formatBRL`             |
| Tabelas BD        | snake_case    | `expenses`, `incomes`   |
| Rotas API         | kebab-case    | `/api/expenses/{id}`    |

- TypeScript em modo strict (`strict: true`)
- PATCH para atualizacao parcial (`exclude_unset=True`)
- `mes_referencia` derivado do path parameter, nunca do body
- Tailwind CSS v4: `@import "tailwindcss"` + `@theme` (NAO usar diretivas v3)

---

## Stack Tecnológica

| Camada         | Tecnologia                  | Versão    |
|----------------|-----------------------------|-----------|
| Frontend       | React + TypeScript          | React 19  |
| Build/Dev      | Vite                        | 6.x       |
| Estilização    | Tailwind CSS                | 4.x       |
| State/Fetch    | TanStack Query              | 5.62+     |
| Routing        | react-router-dom            | 7.x       |
| Auth (FE)      | jwt-decode                  | 4.x       |
| HTTP Client    | fetch nativo                | —         |
| Backend        | Python + FastAPI            | 0.115     |
| Auth (BE)      | python-jose + passlib/bcrypt| 3.3/1.7   |
| Env Config     | python-dotenv               | 1.0+      |
| Email          | SendGrid                    | 6.11      |
| ORM            | SQLAlchemy (sincrono)       | 2.0+      |
| Banco de Dados | PostgreSQL (prod) + SQLite (dev) | —  |
| Migrations     | Alembic                     | 1.14+     |
| Validação      | Pydantic                    | 2.x       |
| Arquitetura    | Monorepo                    | —         |

---

## Contexto Atual do Projeto

### Documentos Existentes
- [x] PRD (`/docs/01-PRD.md`)
- [x] Arquitetura (`/docs/02-ARCHITECTURE.md`)
- [x] Spec Técnica (`/docs/03-SPEC.md`)
- [x] Plano de Implementação (`/docs/04-IMPLEMENTATION-PLAN.md`)
- [x] Guia de Deploy (`/docs/05-DEPLOY-GUIDE.md`)
- [x] Plano de Evolução (`/docs/Plano-de-evolucao.md`)

### Change Requests Ativos
- CR-001: Migracao PostgreSQL + Alembic (concluido)
- CR-002: Multi-usuario + Autenticacao JWT/Google OAuth2 (AR + FN + VL concluidos)
- CR-004: Totalizadores de despesa por status — Pago, Pendente, Atrasado (concluido)
- CR-005: Gastos Diarios — registro de gastos nao planejados com categorias, metodos de pagamento, visao mensal agrupada por dia (concluido)

### Última Tarefa Implementada
- CR-005: Gastos Diarios — modelo DailyExpense, API REST, visao mensal agrupada por dia, ViewSelector para navegacao

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

Referencia rapida de problemas encontrados durante o desenvolvimento e suas solucoes. Consulte esta secao antes de debugar problemas ja resolvidos.

### Dependencias Python

| Problema | Causa | Solucao |
|----------|-------|---------|
| `passlib` falha com bcrypt 4.1+ | passlib 1.7.x nao e compativel com bcrypt >= 4.1 | Manter `bcrypt==4.0.*` fixo em `requirements.txt` |

### Alembic / Migrations

| Problema | Causa | Solucao |
|----------|-------|---------|
| `ALTER TABLE` com FK falha no SQLite | SQLite nao suporta `ALTER` com foreign keys | Usar `op.batch_alter_table()` nas migrations Alembic |

### Ambiente Windows

| Problema | Causa | Solucao |
|----------|-------|---------|
| Comando `del` falha no bash | `del` e comando do CMD, nao do bash | Usar `rm -f` no bash tool |
| `timeout` nao funciona no PowerShell | Comando exclusivo do CMD | Usar `Start-Sleep` no PowerShell |
| `curl` nao funciona no PowerShell | Alias conflita com `Invoke-WebRequest` | Usar `Invoke-RestMethod` no PowerShell |
| uvicorn nao encontrado | Executavel nao esta no PATH do Windows | Usar `python -m uvicorn` |
| `pkill` / `kill` nao encerram processo | Comandos Unix nao funcionam no Windows | Usar `taskkill //F //PID <pid>` |
| Processo Python com nome inesperado | Nome pode ser `python3.12.exe` ao inves de `python.exe` | Identificar via PID: `netstat -ano \| grep <porta>` + `tasklist //FI "PID eq <pid>"` |
