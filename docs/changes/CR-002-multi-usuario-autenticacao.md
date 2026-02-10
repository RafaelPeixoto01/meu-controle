# Change Request — CR-002: Multi-usuario e Autenticacao

**Versao:** 1.0
**Data:** 2026-02-09
**Status:** Rascunho
**Autor:** Claude (Tech Lead)
**Prioridade:** Alta

---

## 1. Resumo da Mudanca

Implementar sistema completo de autenticacao multi-usuario no Meu Controle. O app atualmente opera como MVP single-user sem nenhuma autenticacao. Este CR adiciona:

- Cadastro e login com email/senha
- Login social com Google (OAuth2 direto)
- JWT (access token 15min + refresh token 7 dias) armazenados em localStorage
- Isolamento de dados por usuario (`user_id` em expenses/incomes)
- Recuperacao de senha por email via SendGrid
- Perfil de usuario (visualizar/editar)
- React Router para paginas de autenticacao
- Rotas protegidas no frontend e endpoints protegidos no backend

Corresponde a **Fase 3 — Multi-usuario e Autenticacao** do Roadmap (PRD Secao 9), implementada antes da Fase 2 para que categorias/analytics ja nasçam com isolamento de dados.

---

## 2. Classificacao

| Campo        | Valor                                    |
|--------------|------------------------------------------|
| Tipo         | Nova Feature + Mudanca de Arquitetura    |
| Origem       | Evolucao do produto (Roadmap Fase 3)     |
| Urgencia     | Proxima sprint                           |
| Complexidade | Alta                                     |

---

## 3. Contexto e Motivacao

### Situacao Atual (AS-IS)

- **Sem modelo User:** `models.py` contem apenas `Expense` e `Income`, sem campo `user_id`
- **Sem middleware de auth:** Os 3 routers (`expenses.py`, `incomes.py`, `months.py`) aceitam requisicoes sem autenticacao. Unica dependency injection e `get_db`
- **Sem filtragem por usuario no CRUD:** Todas as 11 funcoes CRUD em `crud.py` operam globalmente — `get_expenses_by_month(db, mes_referencia)` retorna TODAS as expenses do mes
- **Sem escopo de usuario em services:** `generate_month_data()` e `get_monthly_summary()` operam sobre todos os dados
- **Sem headers de auth no frontend:** A funcao `request()` em `api.ts` envia apenas `Content-Type: application/json`
- **Sem roteamento:** `App.tsx` renderiza `MonthlyView` diretamente, sem react-router, login page, ou auth context
- **Sem pacotes de auth:** Backend tem 6 pacotes; frontend tem 3 dependencias

### Problema ou Necessidade

- Qualquer pessoa com acesso a URL pode ver e modificar todos os dados
- Impossivel ter multiplos usuarios com dados isolados
- Pre-requisito para todas as features futuras (Fase 2, 3+)
- Sem autenticacao, o deploy em producao (Railway) expoe dados sem protecao

### Situacao Desejada (TO-BE)

- Usuarios podem se cadastrar com email/senha ou entrar com Google
- JWT access tokens (15min) e refresh tokens (7 dias) gerenciam a sessao
- Cada expense e income pertence a um usuario via FK `user_id`
- Frontend tem paginas de Login, Registro, Recuperacao de Senha, Reset, e Perfil
- React Router gerencia navegacao entre paginas de auth e app principal
- Rotas protegidas redirecionam usuarios nao autenticados para login
- Recuperacao de senha funciona via email (SendGrid)

---

## 4. Detalhamento da Mudanca

### 4.1 O que muda

| #  | Item                         | Antes (AS-IS)                                  | Depois (TO-BE)                                                                       |
|----|------------------------------|-------------------------------------------------|--------------------------------------------------------------------------------------|
| 1  | Modelo de dados              | Apenas `Expense` e `Income`                     | Adiciona `User` e `RefreshToken`; `Expense` e `Income` ganham FK `user_id`           |
| 2  | Indice `mes_referencia`      | Single-column `ix_expenses_mes_referencia`      | Composite `(user_id, mes_referencia)` em ambas tabelas                               |
| 3  | Camada CRUD                  | 11 funcoes sem parametro `user_id`              | Todas recebem `user_id` + 9 novas funcoes para User/RefreshToken                    |
| 4  | Camada Services              | `generate_month_data(db, mes)` sem user         | `generate_month_data(db, mes, user_id)` com escopo por usuario                       |
| 5  | Routers existentes           | Sem dependency de auth                          | Todos endpoints requerem `Depends(get_current_user)` + verificacao de ownership      |
| 6  | Endpoints de API             | 8 endpoints (expenses/incomes/months)           | +10 novos endpoints (`/api/auth/*` e `/api/users/*`)                                 |
| 7  | Frontend routing             | Sem react-router (ADR-002)                      | React Router v6+ com rotas publicas e protegidas                                     |
| 8  | Frontend API client          | `request()` sem headers de auth                 | `Authorization: Bearer <token>` em todas requisicoes + interceptor 401               |
| 9  | Frontend state               | Sem auth context                                | `AuthContext` com login/logout/register, token management em localStorage             |
| 10 | Frontend paginas             | Apenas `MonthlyView`                            | +5 paginas (Login, Register, ForgotPassword, ResetPassword, Profile)                 |
| 11 | Frontend componentes         | Header simples com titulo                       | Header com UserMenu (perfil + logout) + ProtectedRoute                               |
| 12 | Dependencias backend         | 6 pacotes                                       | +5 pacotes (`python-jose`, `passlib`, `python-multipart`, `httpx`, `sendgrid`)       |
| 13 | Dependencias frontend        | 3 pacotes                                       | +2 pacotes (`react-router-dom`, `jwt-decode`)                                        |
| 14 | Variaveis de ambiente        | `DATABASE_URL` apenas                           | +11 novas vars (SECRET_KEY, Google OAuth, SendGrid, etc.)                            |
| 15 | Dados existentes             | Expenses/Incomes sem dono                       | Dados apagados (clean slate); novos dados sempre com `user_id`                       |
| 16 | ADR-002                      | "SPA sem react-router" — Aceita                 | Status: Substituida por ADR-017                                                      |

### 4.2 O que NAO muda

- Campos de Expense e Income (nome, valor, vencimento, parcelas, recorrente, status, data) permanecem identicos
- Shape do `MonthlySummary` response (totais + listas)
- Schemas de input (`ExpenseCreate`, `ExpenseUpdate`, `IncomeCreate`, `IncomeUpdate`) — nenhuma mudanca de campo
- Algoritmo de transicao de mes (RF-06) — apenas adiciona parametro `user_id`
- Logica de auto-deteccao de status (RF-05) — sem mudanca
- Setup Tailwind CSS v4, Vite config, proxy `/api`
- Padroes TanStack Query (staleTime, invalidacao)
- Suporte dual DB (PostgreSQL prod / SQLite dev)
- Endpoint de health check (`/api/health`)

---

## 5. Impacto nos Documentos

| Documento                        | Impactado? | Secoes Afetadas                                                                                          | Acao Necessaria                                                                              |
|----------------------------------|------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| `/docs/01-PRD.md`               | Sim        | Sec 4 (RF), Sec 5 (RNF), Sec 6 (US), Sec 7 (RN), Sec 8 (Fora de Escopo), Sec 9 (Roadmap)              | Adicionar RF-08 a RF-12, remover auth de "fora de escopo", mover Fase 3 para implementada   |
| `/docs/02-ARCHITECTURE.md`      | Sim        | Sec 1 (Stack), Sec 2 (Diagramas), Sec 4 (Modelagem), Sec 5 (API), Sec 6 (Integracoes), Sec 8 (ADRs)   | Adicionar User/RefreshToken ao modelo, ADR-015/016/017, atualizar ADR-002, adicionar Google/SendGrid |
| `/docs/03-SPEC.md`              | Sim        | Adicionar secoes completas para auth endpoints, User model, migration, frontend auth pages                | 4+ novas secoes de feature                                                                   |
| `/docs/04-IMPLEMENTATION-PLAN.md` | Sim      | Adicionar grupo CR-002                                                                                    | 40 novas tarefas em 7 grupos                                                                 |
| `CLAUDE.md`                      | Sim        | Contexto Atual, CRs Ativos, Estrutura de Pastas                                                          | Adicionar CR-002, atualizar pastas e arquivos                                                |

---

## 6. Impacto no Codigo

### 6.1 Arquivos Afetados

#### Backend — Modificar

| Acao      | Caminho                                | Descricao da Mudanca                                                                                 |
|-----------|----------------------------------------|------------------------------------------------------------------------------------------------------|
| Modificar | `backend/app/models.py`               | Adicionar modelos `User` e `RefreshToken`; adicionar FK `user_id` + relationship em `Expense` e `Income` |
| Modificar | `backend/app/schemas.py`              | Adicionar schemas: `UserCreate`, `UserUpdate`, `UserResponse`, `TokenResponse`, `LoginRequest`, `GoogleAuthRequest`, `ForgotPasswordRequest`, `ResetPasswordRequest`, `ChangePasswordRequest` |
| Modificar | `backend/app/crud.py`                 | Adicionar `user_id` a todas as 11 funcoes existentes + 9 novas funcoes para User e RefreshToken      |
| Modificar | `backend/app/services.py`             | Adicionar `user_id` a `generate_month_data()` e `get_monthly_summary()`; propagar para chamadas CRUD |
| Modificar | `backend/app/main.py`                 | Registrar routers `auth` e `users`; atualizar CORS para producao                                     |
| Modificar | `backend/app/routers/expenses.py`     | Adicionar `Depends(get_current_user)` aos 4 endpoints; passar `user_id` ao CRUD; verificar ownership |
| Modificar | `backend/app/routers/incomes.py`      | Mesmo padrao de expenses: auth dependency + user scoping nos 3 endpoints                              |
| Modificar | `backend/app/routers/months.py`       | Adicionar auth dependency; passar `user_id` a `services.get_monthly_summary()`                       |
| Modificar | `backend/requirements.txt`            | Adicionar `python-jose[cryptography]`, `passlib[bcrypt]`, `python-multipart`, `httpx`, `sendgrid`    |
| Modificar | `backend/alembic/env.py`              | Importar `User` e `RefreshToken` para registrar no metadata                                           |

#### Backend — Criar

| Acao  | Caminho                                           | Descricao                                                                                           |
|-------|---------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| Criar | `backend/app/auth.py`                             | Modulo JWT (create/verify token), password hashing (bcrypt), `get_current_user` dependency, Google OAuth token exchange |
| Criar | `backend/app/routers/auth.py`                     | 7 endpoints: register, login, google, refresh, logout, forgot-password, reset-password               |
| Criar | `backend/app/routers/users.py`                    | 3 endpoints: GET /me, PATCH /me, PATCH /me/password                                                 |
| Criar | `backend/app/email_service.py`                    | Integracao SendGrid para envio de email de recuperacao de senha                                       |
| Criar | `backend/alembic/versions/002_add_users_and_auth.py` | Migration: criar tabelas `users` e `refresh_tokens`, limpar dados, adicionar FK `user_id`         |

#### Frontend — Modificar

| Acao      | Caminho                            | Descricao da Mudanca                                                                        |
|-----------|------------------------------------|---------------------------------------------------------------------------------------------|
| Modificar | `frontend/src/main.tsx`           | Envolver app com `BrowserRouter`                                                             |
| Modificar | `frontend/src/App.tsx`            | Reestruturar com `AuthProvider`, `Routes`, `UserMenu` no header, rotas publicas e protegidas |
| Modificar | `frontend/src/services/api.ts`    | Adicionar `Authorization: Bearer` ao `request()`; interceptar 401 para refresh/redirect      |
| Modificar | `frontend/src/types.ts`           | Adicionar tipos `User`, `AuthTokens`, `LoginCredentials`, `RegisterData`, `TokenResponse`    |
| Modificar | `frontend/package.json`           | Adicionar `react-router-dom` e `jwt-decode`                                                  |
| Modificar | `frontend/src/index.css`          | Adicionar cor Google (`--color-google: #4285f4`) ao `@theme`                                 |

#### Frontend — Criar

| Acao  | Caminho                                           | Descricao                                                                                    |
|-------|---------------------------------------------------|----------------------------------------------------------------------------------------------|
| Criar | `frontend/src/contexts/AuthContext.tsx`           | AuthContext + AuthProvider: estado do usuario, tokens em localStorage, login/logout/register   |
| Criar | `frontend/src/hooks/useAuth.ts`                  | Hook de conveniencia: `useAuth()` consome AuthContext                                         |
| Criar | `frontend/src/services/authApi.ts`               | Funcoes de API: loginUser, registerUser, googleAuth, refreshToken, forgotPassword, etc.       |
| Criar | `frontend/src/pages/LoginPage.tsx`               | Formulario email/senha + botao Google + links para registro e recuperacao                     |
| Criar | `frontend/src/pages/RegisterPage.tsx`            | Formulario nome/email/senha/confirmacao + link para login                                     |
| Criar | `frontend/src/pages/ForgotPasswordPage.tsx`      | Input de email para enviar link de recuperacao                                                |
| Criar | `frontend/src/pages/ResetPasswordPage.tsx`       | Formulario nova senha + confirmacao (le token da URL)                                         |
| Criar | `frontend/src/pages/ProfilePage.tsx`             | Visualizar/editar perfil (nome, email) + secao para trocar senha                              |
| Criar | `frontend/src/components/ProtectedRoute.tsx`     | Guard component: redireciona para `/login` se nao autenticado, renderiza `<Outlet />` se sim  |
| Criar | `frontend/src/components/UserMenu.tsx`           | Dropdown no header com nome do usuario, link para Perfil, botao Sair                          |

### 6.2 Banco de Dados

| Acao      | Descricao                                                          | Migration Necessaria? |
|-----------|--------------------------------------------------------------------|------------------------|
| Criar     | Tabela `users` (id, nome, email, password_hash, google_id, avatar_url, email_verified, timestamps) | Sim |
| Criar     | Tabela `refresh_tokens` (id, user_id FK, token_hash, expires_at, created_at) | Sim |
| Limpar    | Apagar todos os registros existentes de `expenses` e `incomes`      | Sim |
| Modificar | Adicionar coluna `user_id VARCHAR(36) NOT NULL FK` em `expenses`    | Sim |
| Modificar | Adicionar coluna `user_id VARCHAR(36) NOT NULL FK` em `incomes`     | Sim |
| Modificar | Substituir indice `ix_expenses_mes_referencia` por `ix_expenses_user_month (user_id, mes_referencia)` | Sim |
| Modificar | Substituir indice `ix_incomes_mes_referencia` por `ix_incomes_user_month (user_id, mes_referencia)` | Sim |

**Migration 002 (pseudocodigo):**

```python
def upgrade():
    # 1. Criar tabela users
    op.create_table("users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),  # nullable para Google-only users
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # 2. Criar tabela refresh_tokens
    op.create_table("refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # 3. Clean slate: apagar dados existentes
    op.execute("DELETE FROM expenses")
    op.execute("DELETE FROM incomes")

    # 4. Remover indices antigos
    op.drop_index("ix_expenses_mes_referencia", table_name="expenses")
    op.drop_index("ix_incomes_mes_referencia", table_name="incomes")

    # 5. Adicionar user_id em expenses e incomes
    op.add_column("expenses", sa.Column("user_id", sa.String(36),
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    op.add_column("incomes", sa.Column("user_id", sa.String(36),
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False))

    # 6. Criar indices compostos
    op.create_index("ix_expenses_user_month", "expenses", ["user_id", "mes_referencia"])
    op.create_index("ix_incomes_user_month", "incomes", ["user_id", "mes_referencia"])


def downgrade():
    op.drop_index("ix_incomes_user_month", table_name="incomes")
    op.drop_index("ix_expenses_user_month", table_name="expenses")
    op.drop_column("incomes", "user_id")
    op.drop_column("expenses", "user_id")
    op.create_index("ix_incomes_mes_referencia", "incomes", ["mes_referencia"])
    op.create_index("ix_expenses_mes_referencia", "expenses", ["mes_referencia"])
    op.drop_table("refresh_tokens")
    op.drop_table("users")
```

---

## 7. Tarefas de Implementacao

### Grupo A: Backend Auth Foundation (Modelos, Schemas, Auth Module, Migration)

| ID      | Tarefa                                                                                   | Depende de | Done When                                                                                                |
|---------|------------------------------------------------------------------------------------------|------------|----------------------------------------------------------------------------------------------------------|
| CR-T-01 | Adicionar dependencias de auth ao `requirements.txt`                                      | —          | `pip install -r requirements.txt` instala `python-jose`, `passlib`, `python-multipart`, `httpx`, `sendgrid` sem erros |
| CR-T-02 | Criar modelos ORM `User` e `RefreshToken` em `models.py`; adicionar FK `user_id` + relationship em `Expense` e `Income` | CR-T-01 | Modelos definem todas colunas. `Expense.user_id` e `Income.user_id` sao `String(36) NOT NULL FK`. Relationships definidas (`User.expenses`, `User.incomes`) |
| CR-T-03 | Adicionar schemas Pydantic de auth em `schemas.py`                                       | CR-T-02    | Schemas compilam: `UserCreate`, `UserUpdate`, `UserResponse`, `TokenResponse`, `LoginRequest`, `GoogleAuthRequest`, `ForgotPasswordRequest`, `ResetPasswordRequest`, `ChangePasswordRequest` |
| CR-T-04 | Criar modulo `backend/app/auth.py` com logica JWT, hashing e dependency `get_current_user` | CR-T-03 | Funcoes: `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `verify_token`, `get_current_user` (FastAPI Depends com OAuth2PasswordBearer). Usa `python-jose` HS256. Vars: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7` |
| CR-T-05 | Criar migration Alembic `002_add_users_and_auth.py`                                       | CR-T-02    | `alembic upgrade head` cria tabelas `users` e `refresh_tokens`, apaga dados existentes, adiciona FK `user_id`, cria indices compostos. `alembic downgrade 001` reverte. Funciona em SQLite e PostgreSQL |
| CR-T-06 | Atualizar `alembic/env.py` para importar novos modelos                                    | CR-T-02    | `User` e `RefreshToken` importados ao lado de `Expense` e `Income` para metadata completo               |

### Grupo B: Backend Auth Endpoints (Auth Router, Email Service, User Router)

| ID      | Tarefa                                                                                    | Depende de      | Done When                                                                                                |
|---------|-------------------------------------------------------------------------------------------|-----------------|----------------------------------------------------------------------------------------------------------|
| CR-T-07 | Criar `backend/app/email_service.py` com integracao SendGrid                               | CR-T-01         | Funcao `send_password_reset_email(to_email, reset_token, user_name)` envia email via API SendGrid. Usa vars `SENDGRID_API_KEY` e `SENDGRID_FROM_EMAIL`. Link no email: `{FRONTEND_URL}/reset-password?token={token}`. Degradacao graciosa se `SENDGRID_API_KEY` nao configurada (loga warning) |
| CR-T-08 | Criar `backend/app/routers/auth.py` com 7 endpoints de autenticacao                       | CR-T-04, CR-T-07 | Endpoints funcionam: `POST /api/auth/register` (201 + tokens), `POST /api/auth/login` (200 + tokens), `POST /api/auth/google` (troca code por info via httpx, cria/vincula usuario), `POST /api/auth/refresh` (valida refresh token no DB, rotaciona, retorna par novo), `POST /api/auth/logout` (invalida refresh token), `POST /api/auth/forgot-password` (gera token 1h, envia email), `POST /api/auth/reset-password` (valida token, atualiza hash) |
| CR-T-09 | Criar `backend/app/routers/users.py` com 3 endpoints de perfil                            | CR-T-04         | `GET /api/users/me` retorna perfil. `PATCH /api/users/me` atualiza nome/email (com check de unicidade). `PATCH /api/users/me/password` valida senha atual e atualiza (rejeita para Google-only user sem password_hash) |
| CR-T-10 | Registrar routers `auth` e `users` em `main.py`                                           | CR-T-08, CR-T-09 | `main.py` inclui ambos routers. Aparecem no Swagger UI em `/docs`                                       |

### Grupo C: Backend Data Scoping (CRUD, Services, Router Auth Integration)

| ID      | Tarefa                                                                                    | Depende de       | Done When                                                                                                |
|---------|-------------------------------------------------------------------------------------------|------------------|----------------------------------------------------------------------------------------------------------|
| CR-T-11 | Adicionar funcoes CRUD para User e RefreshToken em `crud.py`                              | CR-T-05          | Novas funcoes: `get_user_by_email`, `get_user_by_id`, `get_user_by_google_id`, `create_user`, `update_user`, `create_refresh_token`, `get_refresh_token_by_hash`, `delete_refresh_token`, `delete_user_refresh_tokens` |
| CR-T-12 | Adicionar parametro `user_id` a todas funcoes CRUD existentes em `crud.py`                | CR-T-05, CR-T-11 | `get_expenses_by_month(db, mes, user_id)` filtra por ambos. `get_expense_by_id(db, id, user_id)` retorna None se pertence a outro usuario. Mesmo padrao para incomes. `count_expenses_by_month` idem. Funcoes de create/update/delete mantidas (ownership no router) |
| CR-T-13 | Adicionar parametro `user_id` as funcoes de `services.py`                                 | CR-T-12          | `generate_month_data(db, target_mes, user_id)` passa `user_id` a todas chamadas CRUD e seta `user_id` nas novas instancias durante replicacao. `get_monthly_summary(db, mes, user_id)` propaga `user_id` |
| CR-T-14 | Adicionar `Depends(get_current_user)` ao router de expenses e propagar `user_id`          | CR-T-04, CR-T-12 | 4 endpoints requerem auth. `create_expense` seta `user_id=current_user.id`. `update/delete/duplicate` verificam ownership via `get_expense_by_id(db, id, user_id)` |
| CR-T-15 | Adicionar `Depends(get_current_user)` ao router de incomes e propagar `user_id`           | CR-T-04, CR-T-12 | 3 endpoints requerem auth com verificacao de ownership                                                   |
| CR-T-16 | Adicionar `Depends(get_current_user)` ao router de months e propagar `user_id`            | CR-T-04, CR-T-13 | `get_monthly_view` passa `current_user.id` a `services.get_monthly_summary()`                            |

### Grupo D: Frontend Auth Foundation (React Router, Auth Context, Token Management)

| ID      | Tarefa                                                                                    | Depende de       | Done When                                                                                                |
|---------|-------------------------------------------------------------------------------------------|------------------|----------------------------------------------------------------------------------------------------------|
| CR-T-17 | Adicionar `react-router-dom` e `jwt-decode` ao `package.json`                             | —                | `npm install` sucede. Ambos pacotes disponiveis para import                                              |
| CR-T-18 | Adicionar tipos TypeScript de auth em `types.ts`                                          | CR-T-17          | Tipos compilam: `User`, `AuthTokens`, `LoginCredentials`, `RegisterData`, `TokenResponse`                |
| CR-T-19 | Criar `frontend/src/services/authApi.ts` com funcoes de API de auth                       | CR-T-18          | Funcoes compilam: `loginUser`, `registerUser`, `googleAuth`, `refreshTokenApi`, `logoutUser`, `forgotPassword`, `resetPassword`, `getProfile`, `updateProfile`, `changePassword` |
| CR-T-20 | Atualizar `frontend/src/services/api.ts` para incluir token de auth nas requisicoes       | CR-T-18          | `request()` le token de localStorage e adiciona header `Authorization: Bearer`. Em resposta 401, tenta refresh via `/api/auth/refresh`. Se refresh falhar, limpa tokens e redireciona para `/login` |
| CR-T-21 | Criar `frontend/src/contexts/AuthContext.tsx` com AuthProvider                            | CR-T-19, CR-T-20 | AuthContext provê: `user`, `isAuthenticated`, `isLoading`, `login()`, `register()`, `loginWithGoogle()`, `logout()`, `updateUser()`. No mount: checa localStorage, valida token via jwt-decode, seta estado |
| CR-T-22 | Criar `frontend/src/hooks/useAuth.ts` como hook de conveniencia                           | CR-T-21          | `useAuth()` retorna `useContext(AuthContext)` com erro se usado fora do provider                         |
| CR-T-23 | Criar `frontend/src/components/ProtectedRoute.tsx`                                        | CR-T-22          | Checa `isAuthenticated`. Loading = spinner. Nao autenticado = `<Navigate to="/login" />`. Autenticado = `<Outlet />` |
| CR-T-24 | Envolver app com `BrowserRouter` em `main.tsx`                                            | CR-T-17          | `main.tsx` envolve `<App />` com `<BrowserRouter>` dentro de `QueryClientProvider`                       |

### Grupo E: Frontend Auth Pages (Login, Registro, Recuperacao, Perfil)

| ID      | Tarefa                                                                                    | Depende de | Done When                                                                                                |
|---------|-------------------------------------------------------------------------------------------|------------|----------------------------------------------------------------------------------------------------------|
| CR-T-25 | Criar `frontend/src/pages/LoginPage.tsx`                                                  | CR-T-22    | Pagina renderiza: inputs email/senha, botao "Entrar", botao Google, link "Esqueci minha senha" para `/forgot-password`, link "Criar conta" para `/register`. Submit chama `login()`, redireciona para `/` no sucesso. Ja autenticado redireciona para `/` |
| CR-T-26 | Criar `frontend/src/pages/RegisterPage.tsx`                                               | CR-T-22    | Pagina renderiza: inputs nome/email/senha/confirmacao, botao "Criar Conta", link "Ja tenho conta" para `/login`. Valida match de senha client-side. Submit chama `register()`, redireciona para `/` |
| CR-T-27 | Criar `frontend/src/pages/ForgotPasswordPage.tsx`                                         | CR-T-19    | Input email, botao "Enviar link de recuperacao", link "Voltar para login". Submit chama `forgotPassword()`, mostra mensagem "Email enviado" (sempre, por seguranca) |
| CR-T-28 | Criar `frontend/src/pages/ResetPasswordPage.tsx`                                          | CR-T-19    | Le `token` de URL query params (`useSearchParams`). Inputs nova senha/confirmacao, botao "Redefinir Senha". Submit chama `resetPassword(token, newPassword)`, redireciona para `/login` com mensagem de sucesso |
| CR-T-29 | Criar `frontend/src/pages/ProfilePage.tsx`                                                | CR-T-22, CR-T-19 | Mostra info do usuario (nome, email). Modo edicao com form. Secao separada para troca de senha. Chama `updateProfile()` ou `changePassword()`. Rota protegida |

### Grupo F: Frontend Integration (App Restructure, User Menu, Google OAuth UI)

| ID      | Tarefa                                                                                    | Depende de                              | Done When                                                                                                |
|---------|-------------------------------------------------------------------------------------------|-----------------------------------------|----------------------------------------------------------------------------------------------------------|
| CR-T-30 | Criar `frontend/src/components/UserMenu.tsx`                                              | CR-T-22                                 | Dropdown no header: mostra nome do usuario. Menu com "Perfil" (link para `/profile`) e "Sair" (chama `logout()`). Estilizado consistente com header existente |
| CR-T-31 | Reestruturar `App.tsx` com AuthProvider e rotas React Router                              | CR-T-21 a CR-T-30                       | App envolve tudo em `<AuthProvider>`. Rotas publicas: `/login`, `/register`, `/forgot-password`, `/reset-password`. Rotas protegidas (ProtectedRoute): `/` (MonthlyView), `/profile` (ProfilePage). Header com titulo + UserMenu so quando autenticado |
| CR-T-32 | Implementar fluxo Google OAuth no frontend                                                | CR-T-25                                 | Botao Google em LoginPage abre tela de consentimento Google (redirect com `client_id`, `redirect_uri`, `scope=openid email profile`). Callback captura `code` da URL, chama `loginWithGoogle(code)`. Var `VITE_GOOGLE_CLIENT_ID` usada no frontend |
| CR-T-33 | Atualizar `frontend/src/index.css` para estilos de auth                                   | CR-T-25                                 | Adicionada cor Google: `--color-google: #4285f4` ao bloco `@theme`. Convencoes Tailwind v4 mantidas       |

### Grupo G: Testes e Documentacao

| ID      | Tarefa                                                                                    | Depende de       | Done When                                                                                                |
|---------|-------------------------------------------------------------------------------------------|------------------|----------------------------------------------------------------------------------------------------------|
| CR-T-34 | Testar endpoints de auth no backend (Swagger UI)                                          | CR-T-16          | 10 endpoints respondem: register 201 + tokens, login 200 + tokens, email duplicado 409, credenciais invalidas 401, refresh funciona, logout invalida token, forgot-password envia email (ou loga), reset-password funciona |
| CR-T-35 | Testar isolamento de dados multi-usuario                                                   | CR-T-16          | 2 usuarios registrados. User A cria expenses/incomes. User B nao ve/edita/deleta dados de User A. Transicao de mes so replica dados do proprio usuario |
| CR-T-36 | Testar fluxo de auth no frontend end-to-end                                               | CR-T-31          | Fluxo completo: registrar -> auto-login -> dashboard vazio -> criar dados -> logout -> login -> ver mesmos dados. Rotas protegidas redirecionam. Login redireciona quando ja autenticado |
| CR-T-37 | Testar fluxo Google OAuth                                                                 | CR-T-32          | Google login cria usuario (ou vincula email existente), retorna tokens, usuario ve dashboard. Perfil mostra avatar_url se disponivel |
| CR-T-38 | Testar fluxo de recuperacao de senha                                                      | CR-T-28, CR-T-07 | Forgot password envia email (checar SendGrid ou logs). Link de reset funciona, usuario define nova senha e faz login com ela |
| CR-T-39 | Testar fluxo de refresh token                                                             | CR-T-20          | Access token expira apos 15min. Frontend automaticamente renova via refresh token. Se refresh token expirado, redireciona para login |
| CR-T-40 | Atualizar documentacao do projeto (PRD, Arquitetura, Spec, Plano, CLAUDE.md)              | CR-T-36          | PRD adiciona RF-08 a RF-12. Arquitetura adiciona modelos User/RefreshToken, ADR-015/016/017, atualiza ADR-002. Spec adiciona secoes de auth. Plano adiciona grupo CR-002. CLAUDE.md atualiza contexto |

---

## 8. Criterios de Aceite

- [ ] Novo usuario pode se cadastrar com nome, email e senha
- [ ] Usuario cadastrado pode fazer login com email e senha
- [ ] Usuario pode fazer login com conta Google (OAuth2)
- [ ] Login Google vincula a conta existente se mesmo email
- [ ] Access token expira apos 15 minutos
- [ ] Refresh token renova access token automaticamente
- [ ] Refresh token expira apos 7 dias, exigindo re-login
- [ ] Logout invalida refresh token no banco de dados
- [ ] Usuario pode solicitar email de recuperacao de senha
- [ ] Link de reset de senha funciona com token temporario (1 hora)
- [ ] Usuario pode visualizar e editar perfil (nome, email)
- [ ] Usuario pode trocar senha pela pagina de perfil
- [ ] Todos endpoints de expenses exigem autenticacao
- [ ] Todos endpoints de incomes exigem autenticacao
- [ ] Endpoint de visao mensal exige autenticacao
- [ ] User A nao pode ver/editar/deletar expenses ou incomes de User B
- [ ] Transicao de mes (RF-06) replica apenas dados do usuario atual
- [ ] Auto-deteccao de status (RF-05) afeta apenas expenses do usuario atual
- [ ] Requisicoes nao autenticadas retornam 401
- [ ] Frontend redireciona usuarios nao autenticados para pagina de login
- [ ] Frontend mostra UserMenu com opcoes de perfil e logout
- [ ] Frontend trata respostas 401 tentando refresh token
- [ ] Dados existentes apagados na migration (clean slate)
- [ ] Migration roda com sucesso em SQLite e PostgreSQL
- [ ] `alembic downgrade 001` reverte a migration corretamente
- [ ] Todos documentos atualizados para refletir mudancas de auth

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                                                      | Probabilidade | Impacto  | Mitigacao                                                                                  |
|----|-------------------------------------------------------------------------------|---------------|----------|--------------------------------------------------------------------------------------------|
| 1  | `SECRET_KEY` nao configurada em producao — tokens assinados com default fraco | Alta          | Critico  | Exigir `SECRET_KEY` via env var. Lancar erro no startup se nao setada e `DATABASE_URL` aponta para PostgreSQL |
| 2  | Google OAuth requer HTTPS para redirect URI em producao                        | Media         | Alto     | Railway fornece HTTPS por padrao. Documentar requisito de `GOOGLE_REDIRECT_URI`            |
| 3  | `SENDGRID_API_KEY` nao configurada impede recuperacao de senha                 | Media         | Medio    | Degradacao graciosa: loga warning se nao setada. Endpoint retorna 200 (seguranca: nao revela se email existe) |
| 4  | SQLite nao aplica FK constraints por padrao                                   | Media         | Medio    | Adicionar `PRAGMA foreign_keys = ON` em engine connect event para SQLite                   |
| 5  | Token em localStorage vulneravel a XSS                                        | Baixa         | Alto     | Aceitavel para MVP. Mitigado por CSP headers e ausencia de HTML gerado por usuario. Documentar como limitacao conhecida |
| 6  | Migration 002 apaga todos os dados (decisao clean slate)                      | Baixa         | Medio    | Decisao explicita do usuario. Documentar na migration. Railway: fazer backup PostgreSQL antes |
| 7  | Race condition: duas requisicoes simultaneas de refresh token                  | Baixa         | Baixo    | Implementar rotacao de token: refresh token antigo invalidado no uso. Segunda requisicao falha, usuario re-loga |
| 8  | Google OAuth token exchange requer chamada backend->Google (httpx)             | Baixa         | Medio    | httpx e bem testado. Tratar timeout e erros de conexao graciosamente                       |
| 9  | Adicionar react-router muda comportamento de SPA fallback                     | Media         | Medio    | Backend `serve_spa` em `main.py` serve `index.html` para rotas nao-API — React Router cuida do client-side routing |
| 10 | Esquecimento de `user_id` em alguma chamada CRUD durante transicao de mes      | Media         | Alto     | Testar explicitamente multi-usuario em `generate_month_data()`. Adicionar checagem em cada CRUD |

---

## 10. Plano de Rollback

1. **Reverter commits:** `git revert` de todos os commits CR-002 (serao sequenciais por grupo)
2. **Reverter migration:** `alembic downgrade 001` remove tabelas users/refresh_tokens e colunas user_id. Nota: dados criados apos migration serao perdidos
3. **Frontend:** Remover `react-router-dom` e `jwt-decode` do `package.json`, rodar `npm install`
4. **Backend:** Remover `python-jose`, `passlib`, `python-multipart`, `httpx`, `sendgrid` do `requirements.txt`, rodar `pip install -r requirements.txt`
5. **Variaveis de ambiente:** Remover `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `FRONTEND_URL` do Railway
6. **Google OAuth:** Revogar/deletar app OAuth no Google Cloud Console (opcional)

---

## Anexo A: Novas ADRs

### ADR-015: JWT tokens em localStorage

- **Status:** Aceita
- **Data:** 2026-02-09
- **Contexto:** Armazenar tokens JWT no frontend para autenticacao de SPA.
- **Decisao:** Usar localStorage para access token (15min) e refresh token (7 dias).
- **Alternativas Descartadas:**
  - httpOnly cookies: Mais seguro contra XSS, mas adiciona complexidade de CSRF e complica proxy Vite.
  - sessionStorage: Tokens perdidos ao fechar aba. UX ruim.
- **Consequencias:** Implementacao simples. Vulneravel a XSS (mitigado pela ausencia de conteudo gerado por usuario).

### ADR-016: Google OAuth2 direto (sem Firebase/Auth0)

- **Status:** Aceita
- **Data:** 2026-02-09
- **Contexto:** Oferecer login social com Google alem de email/senha.
- **Decisao:** Implementar Google OAuth2 via Authorization Code flow. Frontend redireciona para Google, backend troca code por tokens via httpx.
- **Alternativas Descartadas:**
  - Firebase Auth: Dependencia de servico externo.
  - Auth0/Clerk: Custo adicional e dependencia.
- **Consequencias:** Controle total, sem custos externos. Requer configurar Google Cloud Console.

### ADR-017: Adotar React Router (substitui ADR-002)

- **Status:** Aceita (substitui ADR-002)
- **Data:** 2026-02-09
- **Contexto:** Com autenticacao, o app precisa de multiplas paginas (login, register, forgot-password, reset-password, profile, dashboard).
- **Decisao:** Adotar react-router-dom v6+ para rotas client-side.
- **Alternativas Descartadas:**
  - Renderizacao condicional sem router: Inviavel com 6+ paginas e deep-linking necessario (reset-password token via URL).
- **Consequencias:** URLs semanticas, deep-linking funcional, layout aninhado com ProtectedRoute. SPA fallback do backend ja funciona.

---

## Anexo B: Novas Variaveis de Ambiente

| Variavel                      | Obrigatoria          | Default                                      | Descricao                                      |
|-------------------------------|----------------------|----------------------------------------------|-------------------------------------------------|
| `SECRET_KEY`                  | Sim (producao)       | `"dev-secret-key-change-in-production"`      | Chave para assinar JWTs                         |
| `ALGORITHM`                   | Nao                  | `"HS256"`                                    | Algoritmo JWT                                   |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Nao                  | `15`                                         | Vida util do access token (minutos)             |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Nao                  | `7`                                          | Vida util do refresh token (dias)               |
| `GOOGLE_CLIENT_ID`            | Sim (Google login)   | —                                            | ID do app OAuth no Google Cloud Console         |
| `GOOGLE_CLIENT_SECRET`        | Sim (Google login)   | —                                            | Secret do app OAuth no Google Cloud Console     |
| `GOOGLE_REDIRECT_URI`         | Sim (Google login)   | —                                            | URI de callback OAuth                           |
| `SENDGRID_API_KEY`            | Sim (recovery email) | —                                            | API key do SendGrid                             |
| `SENDGRID_FROM_EMAIL`         | Sim (recovery email) | —                                            | Email remetente (verificado no SendGrid)        |
| `FRONTEND_URL`                | Sim                  | `"http://localhost:5173"`                    | URL base do frontend (para links em emails)     |
| `VITE_GOOGLE_CLIENT_ID`       | Sim (frontend)       | —                                            | Mesmo GOOGLE_CLIENT_ID, exposto ao Vite         |

---

## Anexo C: Novos Endpoints de API

| Metodo | Rota                            | Auth?   | Request Body                                   | Response                          | Status Codes     |
|--------|----------------------------------|---------|------------------------------------------------|-----------------------------------|------------------|
| POST   | `/api/auth/register`            | Nao     | `{ nome, email, password }`                    | `{ access_token, refresh_token, token_type, user }` | 201, 409, 422 |
| POST   | `/api/auth/login`               | Nao     | `{ email, password }`                          | `{ access_token, refresh_token, token_type, user }` | 200, 401, 422 |
| POST   | `/api/auth/google`              | Nao     | `{ code }`                                     | `{ access_token, refresh_token, token_type, user }` | 200, 400      |
| POST   | `/api/auth/refresh`             | Nao     | `{ refresh_token }`                            | `{ access_token, refresh_token, token_type }`        | 200, 401      |
| POST   | `/api/auth/logout`              | Sim     | `{ refresh_token }`                            | `{ message }`                     | 200              |
| POST   | `/api/auth/forgot-password`     | Nao     | `{ email }`                                    | `{ message }`                     | 200              |
| POST   | `/api/auth/reset-password`      | Nao     | `{ token, new_password }`                      | `{ message }`                     | 200, 400         |
| GET    | `/api/users/me`                 | Sim     | —                                              | `UserResponse`                    | 200, 401         |
| PATCH  | `/api/users/me`                 | Sim     | `{ nome?, email? }`                            | `UserResponse`                    | 200, 409, 401    |
| PATCH  | `/api/users/me/password`        | Sim     | `{ current_password, new_password }`           | `{ message }`                     | 200, 400, 401    |

---

## Anexo D: Frontend Routes

| Rota                | Pagina              | Protegida? | Descricao                           |
|---------------------|---------------------|------------|-------------------------------------|
| `/login`            | LoginPage           | Nao        | Formulario de login + Google        |
| `/register`         | RegisterPage        | Nao        | Formulario de cadastro              |
| `/forgot-password`  | ForgotPasswordPage  | Nao        | Input de email para recuperacao     |
| `/reset-password`   | ResetPasswordPage   | Nao        | Nova senha (token via query param)  |
| `/`                 | MonthlyView         | Sim        | Dashboard principal (expenses/incomes) |
| `/profile`          | ProfilePage         | Sim        | Visualizar/editar perfil + trocar senha |

---

## Changelog

| Data       | Autor            | Descricao          |
|------------|------------------|--------------------|
| 2026-02-09 | Claude (Tech Lead) | CR criado (v1.0) |
