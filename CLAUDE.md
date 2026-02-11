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

### Regra de Ouro

```
Documentação PRIMEIRO → Código DEPOIS
```

- Novas features: PRD → Arquitetura → Spec → Plano → Implementação
- Alterações/Correções: CR → Avaliar impacto → Atualizar docs afetados → Implementar
- Bug fix simples: CR → Implementar → Atualizar testes

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

### Durante a Implementação

- Siga a estrutura de pastas do `02-ARCHITECTURE.md`
- Siga as convenções de nomenclatura do `02-ARCHITECTURE.md`
- Implemente uma tarefa por vez conforme o `04-IMPLEMENTATION-PLAN.md`
- Escreva testes para cada funcionalidade
- Verifique o critério "Done When" de cada tarefa ao concluir

### Commits

- Formato: Conventional Commits
- Nova feature: `feat: implement T-XXX - [descrição]`
- Correção: `fix: CR-XXX - [descrição]`
- Documentação: `docs: update [documento] for CR-XXX`
- Refactoring: `refactor: [descrição]`
- Testes: `test: add tests for T-XXX`

---

## Regras para Alterações e Correções

Quando eu pedir uma alteração, correção ou nova funcionalidade em algo que já existe:

1. **Crie um Change Request (CR)** usando o template em `/docs/templates/00-template-change-request.md`
2. **Salve** em `/docs/changes/CR-[XXX]-[slug].md` (numere sequencialmente)
3. **Avalie o impacto** nos documentos existentes (PRD, Arquitetura, Spec, Plano)
4. **Atualize os documentos afetados** antes de implementar
5. **Implemente** seguindo as tarefas do CR
6. **Valide** os critérios de aceite

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
│       └── 002_add_users_and_auth.py  # CR-002
│   └── app/
│       ├── __init__.py
│       ├── main.py           # Entry point FastAPI + lifespan
│       ├── database.py       # Engine SQLAlchemy + SessionLocal
│       ├── models.py         # ORM: User, Expense, Income, RefreshToken
│       ├── schemas.py        # Pydantic: request/response + auth schemas
│       ├── crud.py           # Acesso a dados + User/RefreshToken CRUD
│       ├── services.py       # Logica: transicao de mes, auto-status (user_id)
│       ├── auth.py           # CR-002: JWT + bcrypt auth module
│       ├── email_service.py  # CR-002: SendGrid email (password reset)
│       └── routers/
│           ├── auth.py       # CR-002: register, login, Google OAuth, refresh, logout, forgot/reset password
│           ├── users.py      # CR-002: GET/PATCH /me, change password
│           ├── expenses.py   # CRUD + duplicate (auth required)
│           ├── incomes.py    # CRUD (auth required)
│           └── months.py     # GET visao mensal (auth required)
├── frontend/
│   ├── package.json
│   ├── vite.config.ts        # Proxy /api -> :8000
│   ├── index.html
│   └── src/
│       ├── main.tsx          # Bootstrap React + QueryClient + BrowserRouter
│       ├── App.tsx           # Shell com AuthProvider + Routes
│       ├── index.css         # Tailwind v4 (@import + @theme)
│       ├── vite-env.d.ts     # Vite client types
│       ├── types.ts          # Tipos + Auth types (CR-002)
│       ├── utils/            # format.ts, date.ts
│       ├── services/
│       │   ├── api.ts        # HTTP client com auth header + 401 interceptor
│       │   └── authApi.ts    # CR-002: auth API functions
│       ├── contexts/
│       │   └── AuthContext.tsx  # CR-002: auth state management
│       ├── hooks/            # useExpenses, useIncomes, useMonthTransition, useAuth
│       ├── components/       # MonthNavigator, Tables, Forms, Modals, ProtectedRoute, UserMenu
│       └── pages/            # MonthlyView, Login, Register, ForgotPassword, ResetPassword, Profile
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

### Change Requests Ativos
- CR-001: Migracao PostgreSQL + Alembic (concluido)
- CR-002: Multi-usuario + Autenticacao JWT/Google OAuth2 (AR + FN + VL concluidos)

### Última Tarefa Implementada
- Fix Google OAuth producao: endpoint `GET /api/config` serve `google_client_id` em runtime (elimina dependencia de build-time env vars)

---

## Lembretes Importantes

- **Pergunte antes de assumir.** Se algo não está claro na spec, pergunte.
- **Não corrija o que não foi pedido.** Foque apenas no escopo da tarefa.
- **Testes são obrigatórios.** Toda funcionalidade precisa de cobertura.
- **Um passo de cada vez.** Implemente por grupo/tarefa, não tudo de uma vez.
- **Documente primeiro.** Código sem documentação gera retrabalho.
