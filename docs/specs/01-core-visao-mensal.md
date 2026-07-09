# Spec — Core: Visão Mensal (RF-01..RF-07, RF-13)

> Extraído de `docs/03-SPEC.md` no CR-038 (conteúdo original preservado). Índice: [03-SPEC.md](../03-SPEC.md)

# Especificacao Tecnica — Meu Controle (Fase 1 + 3 + Gastos Diarios + Dashboard + Projecao de Parcelas + Score + Alertas)

**Versao:** 2.9
**Data:** 2026-03-18
**PRD Ref:** 01-PRD v2.3
**Arquitetura Ref:** 02-ARCHITECTURE v2.9
**CR Ref:** CR-002 (Multi-usuario e Autenticacao), CR-005 (Gastos Diarios), CR-007 (Consulta Parcelas), CR-010 (Hardening de Seguranca), CR-011 (Calculadora de Selecao de Despesas), CR-012 (Responsividade Frontend), CR-016 (Categorizacao de Despesas), CR-019 (Dashboard Visual), CR-021 (Visao Consolidada de Parcelas Futuras), CR-026 (Score de Saude Financeira), CR-033 (Alertas e Notificacoes Inteligentes)

---

## 1. Resumo das Mudancas

Fase 1 implementa o MVP completo do Meu Controle: aplicacao web para controle financeiro pessoal mensal com CRUD de despesas e receitas, visao mensal consolidada com totalizadores, transicao automatica de mes e gestao de status de pagamento. Fase 3 (CR-002) adiciona autenticacao multi-usuario com JWT, login social Google OAuth2, recuperacao de senha via email, perfil de usuario e isolamento de dados por `user_id`. CR-005 adiciona Gastos Diarios: CRUD de gastos nao planejados com categorias fixas, visao mensal agrupada por dia e navegacao via ViewSelector.

### 3.2. Parcelamento (CR-007 Atualizado)

- **Criação**: No endpoint `POST /expenses`, se `parcela_total > 1`:
  - O backend deve iterar de `i=0` até `parcela_total - 1`.
  - Calcular `mes_referencia` e `vencimento` incrementando `i` meses.
  - Criar e persistir `Expense` para cada mês.
  - Isso substitui a estratégia anterior de "Lazy Creation".

- **Consulta**: O endpoint `GET /expenses/installments` agrupa registros existentes baseando-se em `nome` e `parcela_total`. Como agora todos os registros existem, o cálculo de `valor_restante` e `total_pendente` será preciso imediatamente.

### Escopo desta Iteracao

**Fase 1 — Features base:**
- Infraestrutura (backend FastAPI + frontend React/Vite)
- CRUD de Despesas (RF-01) com gestao de status (RF-05) e duplicacao (RF-07)
- CRUD de Receitas (RF-02)
- Visao Mensal com totalizadores (RF-03, RF-04)
- Transicao Automatica de Mes (RF-06)

**Fase 3 — Autenticacao e Multi-usuario (CR-002):**
- Cadastro e login com email/senha (RF-08, RF-09)
- Login social com Google OAuth2 (RF-09)
- Gestao de sessao com JWT access/refresh tokens (RF-10)
- Isolamento de dados por usuario — `user_id` FK em expenses/incomes (RF-10, RN-015)
- Recuperacao de senha via email SendGrid (RF-11)
- Perfil de usuario — visualizar/editar (RF-12)
- React Router para paginas de auth (ADR-017)
- Retrofit de features existentes com auth dependency e user scoping

**Gastos Diarios (CR-005):**
- CRUD de gastos diarios nao planejados (RF-13)
- Categorias fixas (14 + Outros) com subcategorias, definidas em `categories.py`
- 6 metodos de pagamento (Dinheiro, Cartao de Credito/Debito, Pix, Vale Alimentacao/Refeicao)
- Visao mensal agrupada por dia com subtotais e total do mes
- ViewSelector para alternar entre Gastos Planejados e Gastos Diarios
- Rota `/daily-expenses` protegida com autenticacao

**Consulta de Parcelas (CR-007):**
- Endpoint `/api/expenses/installments` para listar todas as parcelas de compras parceladas (`parcela_total > 1`)
- Nova tela `InstallmentsView` acessivel pelo ViewSelector ou Menu
- Exibicao de cards totalizadores: Total Gasto, Total Pago, Total Pendente, Total Atrasado

**Agrupamento de Parcelas por Status (CR-015):**
- Grupos de parcelamento separados em duas secoes: "Em Andamento" (primeiro) e "Concluidos" (depois)
- Cada secao exibe header com titulo e badge de contagem
- Secoes vazias ficam ocultas automaticamente

---

## 2. Detalhamento Tecnico

### Contratos da API (Visao Geral)

| Metodo   | Path                                   | Auth? | Body                    | Resposta                | Descricao                                      |
|----------|----------------------------------------|-------|-------------------------|-------------------------|-------------------------------------------------|
| `GET`    | `/api/months/{year}/{month}`           | Sim   | —                       | `MonthlySummary`        | Visao mensal completa. Dispara RF-06 + RF-05.   |
| `POST`   | `/api/expenses/{year}/{month}`         | Sim   | `ExpenseCreate`         | `ExpenseResponse` (201) | Criar despesa no mes                            |
| `PATCH`  | `/api/expenses/{expense_id}`           | Sim   | `ExpenseUpdate`         | `ExpenseResponse`       | Atualizar campos da despesa                     |
| `DELETE` | `/api/expenses/{expense_id}`           | Sim   | — (`?delete_all=...`)   | 204 No Content          | Excluir despesa (com exclusão em série CR-009)  |
| `POST`   | `/api/expenses/{expense_id}/duplicate` | Sim   | —                       | `ExpenseResponse` (201) | RF-07: Duplicar despesa                         |
| `POST`   | `/api/incomes/{year}/{month}`          | Sim   | `IncomeCreate`          | `IncomeResponse` (201)  | Criar receita no mes                            |
| `PATCH`  | `/api/incomes/{income_id}`             | Sim   | `IncomeUpdate`          | `IncomeResponse`        | Atualizar campos da receita                     |
| `DELETE` | `/api/incomes/{income_id}`             | Sim   | —                       | 204 No Content          | Excluir receita                                 |
| `POST`   | `/api/auth/register`                   | Nao   | `UserCreate`            | `TokenResponse` (201)   | CR-002: Cadastro de usuario (RF-08)             |
| `POST`   | `/api/auth/login`                      | Nao   | `LoginRequest`          | `TokenResponse`         | CR-002: Login email/senha (RF-09)               |
| `POST`   | `/api/auth/google`                     | Nao   | `GoogleAuthRequest`     | `TokenResponse`         | CR-002: Login Google OAuth2 (RF-09)             |
| `POST`   | `/api/auth/refresh`                    | Nao   | — (lê cookie HttpOnly)  | `TokenResponse`         | CR-002/CR-010: Renovar tokens (RF-10)           |
| `POST`   | `/api/auth/logout`                     | Sim   | — (lê cookie HttpOnly)  | `{"message": "..."}`    | CR-002/CR-010: Invalidar refresh token (RF-10)  |
| `POST`   | `/api/auth/forgot-password`            | Nao   | `ForgotPasswordRequest` | `{"message": "..."}`    | CR-002: Solicitar reset de senha (RF-11)        |
| `POST`   | `/api/auth/reset-password`             | Nao   | `ResetPasswordRequest`  | `{"message": "..."}`    | CR-002: Redefinir senha (RF-11)                 |
| `GET`    | `/api/users/me`                        | Sim   | —                       | `UserResponse`          | CR-002: Perfil do usuario (RF-12)               |
| `PATCH`  | `/api/users/me`                        | Sim   | `UserUpdate`            | `UserResponse`          | CR-002: Atualizar perfil (RF-12)                |
| `PATCH`  | `/api/users/me/password`               | Sim   | `ChangePasswordRequest` | `{"message": "..."}`    | CR-002: Trocar senha (RF-12)                    |
| `GET`    | `/api/config`                          | Nao   | —                       | `{ google_client_id: string }` | Configuracao publica (Google Client ID runtime) |
| `GET`    | `/api/daily-expenses/categories`       | Nao   | —                       | `CategoriesResponse`    | CR-005: Categorias + metodos de pagamento       |
| `GET`    | `/api/expenses/categories`             | Sim   | —                       | `{ categorias: {...} }` | CR-016: Categorias para despesas planejadas     |
| `GET`    | `/api/expenses/installments`           | Sim   | —                       | `InstallmentsSummary`   | CR-007: Lista de parcelas + totalizadores       |
| `GET`    | `/api/daily-expenses/{year}/{month}`   | Sim   | —                       | `DailyExpenseMonthlySummary` | CR-005: Visao mensal agrupada por dia      |
| `POST`   | `/api/daily-expenses/{year}/{month}`   | Sim   | `DailyExpenseCreate`    | `DailyExpenseResponse` (201) | CR-005: Criar gasto diario               |
| `PATCH`  | `/api/daily-expenses/{id}`             | Sim   | `DailyExpenseUpdate`    | `DailyExpenseResponse`  | CR-005: Atualizar gasto diario                  |
| `DELETE` | `/api/daily-expenses/{id}`             | Sim   | —                       | 204 No Content          | CR-005: Excluir gasto diario                    |
| `GET`    | `/api/alerts`                          | Sim   | —                       | `AlertasResponse`       | CR-033: Lista alertas ativos + resumo           |
| `PATCH`  | `/api/alerts/{id}/seen`                | Sim   | —                       | `AlertaOutput`          | CR-033: Marcar alerta como visto                |
| `PATCH`  | `/api/alerts/{id}/dismiss`             | Sim   | —                       | `AlertaOutput`          | CR-033: Dispensar alerta                        |
| `GET`    | `/api/alerts/config`                   | Sim   | —                       | `ConfiguracaoAlertasResponse` | CR-033: Obter configuracoes de alertas    |
| `PUT`    | `/api/alerts/config`                   | Sim   | `ConfiguracaoAlertasUpdate` | `ConfiguracaoAlertasResponse` | CR-033: Atualizar configuracoes       |
| `GET`    | `/api/health`                          | Nao   | —                       | `{"status": "ok"}`      | Health check                                    |

**Nota:** O endpoint principal e `GET /api/months/{year}/{month}`. Ele retorna tudo que o frontend precisa em uma unica chamada: despesas, receitas e totalizadores. Tambem dispara a geracao automatica de mes (RF-06) e a auto-deteccao de status (RF-05).

**Nota (CR-002):** Endpoints marcados com `Auth: Sim` requerem header `Authorization: Bearer <access_token>`. Requisicoes sem token ou com token invalido/expirado retornam 401 Unauthorized. Endpoints de expenses/incomes/months tambem verificam ownership — um usuario so acessa seus proprios dados (RN-015).

---

### Feature: Infraestrutura e Setup

#### 2.1 Descricao Tecnica

Configuracao base do projeto: backend FastAPI com SQLAlchemy/SQLite e frontend React com Vite, Tailwind CSS v4 e TanStack Query. Para decisoes arquiteturais, ver ADRs em 02-ARCHITECTURE.md.

#### 2.2 Arquivos

| Acao  | Caminho                           | Descricao                                         |
|-------|-----------------------------------|----------------------------------------------------|
| Criar | `backend/requirements.txt`        | Dependencias Python pinadas                        |
| Criar | `backend/app/__init__.py`         | Pacote Python (vazio)                              |
| Criar | `backend/app/database.py`         | Engine SQLAlchemy, sessoes, Base, dependency injection |
| Criar | `backend/app/main.py`             | Entry point FastAPI: lifespan, CORS, routers       |
| Criar | `backend/app/routers/__init__.py` | Pacote routers (vazio)                             |
| Criar | `frontend/package.json`           | Dependencias e scripts npm                         |
| Criar | `frontend/vite.config.ts`         | Build config + proxy /api                          |
| Criar | `frontend/tsconfig.json`          | Config raiz TypeScript                             |
| Criar | `frontend/tsconfig.app.json`      | Opcoes do compilador TS                            |
| Criar | `frontend/index.html`             | HTML entry point da SPA                            |
| Criar | `frontend/src/index.css`          | Tailwind v4 import + tema customizado              |
| Criar | `frontend/src/main.tsx`           | Bootstrap React + QueryClient                      |
| Criar | `frontend/src/App.tsx`            | Shell da aplicacao com header                      |
| Criar | `.gitignore`                      | Exclusoes para Python, Node, SQLite, IDE           |

#### 2.3 Codigo

**`backend/requirements.txt`**

```
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy==2.0.*
pydantic==2.*
psycopg2-binary==2.9.*
alembic==1.14.*
python-jose[cryptography]==3.3.*
passlib[bcrypt]==1.7.*
python-multipart==0.0.*
httpx==0.27.*
sendgrid==6.11.*
```

> **CR-002:** 5 novas dependencias para autenticacao (JWT, hashing, form data, Google OAuth HTTP client, email).

**`backend/app/database.py`** (CR-001: DATABASE_URL via env var, engine condicional)

```python
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///meu_controle.db")

# Railway PostgreSQL usa "postgres://" mas SQLAlchemy exige "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency injection: fornece sessao do banco e garante cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**`backend/app/main.py`** (CR-001: Alembic gerencia migrations; CR-002: routers auth e users)

```python
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import expenses, incomes, months, auth, users  # CR-002: auth, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: migrations gerenciadas pelo Alembic (ver CR-001)
    yield


app = FastAPI(
    title="Meu Controle API",
    version="2.0.0",  # CR-002
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)    # CR-002: autenticacao (register, login, Google, refresh, logout, forgot/reset password)
app.include_router(users.router)   # CR-002: perfil de usuario (GET/PATCH /me, change password)
app.include_router(months.router)
app.include_router(expenses.router)
app.include_router(incomes.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/config")
def get_public_config():
    """Return public configuration (no secrets)."""
    import os
    return {
        "google_client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
    }


# Serve frontend static files in production
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve index.html for all non-API routes (SPA fallback)."""
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
```

**Comandos para rodar (desenvolvimento):**
1. `alembic upgrade head` — aplica migrations (a partir do diretorio `backend/`)
2. `uvicorn app.main:app --reload` — inicia o servidor

**`frontend/package.json`**

```json
{
  "name": "meu-controle-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.62.0",
    "react-router-dom": "^7.0.0",
    "jwt-decode": "^4.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@tailwindcss/vite": "^4.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0"
  }
}
```

**`frontend/vite.config.ts`**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

**`frontend/tsconfig.json`**

```json
{
  "files": [],
  "references": [{ "path": "./tsconfig.app.json" }]
}
```

**`frontend/tsconfig.app.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "isolatedModules": true,
    "skipLibCheck": true
  },
  "include": ["src"]
}
```

**`frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Meu Controle</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**`frontend/src/index.css`**

```css
@import "tailwindcss";

@theme {
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-danger: #dc2626;
  --color-success: #16a34a;
  --color-warning: #d97706;
  --color-pendente: #eab308;
  --color-pago: #16a34a;
  --color-atrasado: #dc2626;
  --color-google: #4285f4;
}
```

**`frontend/src/main.tsx`** (CR-002: BrowserRouter para rotas client-side)

```typescript
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";  // CR-002: ADR-017
import App from "./App";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutos
      retry: 1,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>
);
```

**`frontend/src/App.tsx`** (CR-002: AuthProvider, React Router, ProtectedRoute, UserMenu)

```typescript
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { useAuth } from "./hooks/useAuth";
import ProtectedRoute from "./components/ProtectedRoute";
import UserMenu from "./components/UserMenu";
import MonthlyView from "./pages/MonthlyView";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import ProfilePage from "./pages/ProfilePage";

function AppHeader() {
  const { isAuthenticated } = useAuth();
  return (
    <header className="bg-primary text-white py-4 px-6 shadow-md flex justify-between items-center">
      <h1 className="text-xl font-bold tracking-wide">MEU CONTROLE</h1>
      {isAuthenticated && <UserMenu />}
    </header>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-50">
        <AppHeader />
        <main>
          <Routes>
            {/* Rotas publicas */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            {/* Rotas protegidas */}
            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<MonthlyView />} />
              <Route path="/profile" element={<ProfilePage />} />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </AuthProvider>
  );
}
```

**`.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
*.egg
dist/
build/
.venv/
venv/

# SQLite
*.db

# Node
node_modules/
frontend/dist/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Env
.env
.env.local
```

---

### Feature: [RF-01] CRUD de Despesas

#### 2.1 Descricao Tecnica

Implementa criacao, leitura, edicao e exclusao de despesas mensais. Cada despesa pertence a um mes de referencia e possui status de pagamento, campos opcionais de parcelamento e flag de recorrencia.

#### 2.2 Arquivos

| Acao  | Caminho                              | Descricao                              |
|-------|--------------------------------------|----------------------------------------|
| Criar | `backend/app/models.py`              | Modelo ORM Expense + enum ExpenseStatus |
| Criar | `backend/app/schemas.py`             | Schemas Pydantic: ExpenseCreate, ExpenseUpdate, ExpenseResponse |
| Criar | `backend/app/crud.py`                | Funcoes de acesso a dados para expenses |
| Criar | `backend/app/routers/expenses.py`    | Endpoints POST, PATCH, DELETE          |
| Criar | `frontend/src/types.ts`              | Types TypeScript: Expense, ExpenseCreate, ExpenseUpdate |
| Criar | `frontend/src/services/api.ts`       | Funcoes HTTP: createExpense, updateExpense, deleteExpense |
| Criar | `frontend/src/hooks/useExpenses.ts`  | Hooks TanStack Query para mutations    |

#### 2.3 Interfaces / Types

**Backend — Models (`backend/app/models.py`):**

```python
import uuid
import enum
from datetime import date, datetime

from sqlalchemy import String, Date, Boolean, Integer, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseStatus(str, enum.Enum):
    PENDENTE = "Pendente"
    PAGO = "Pago"
    ATRASADO = "Atrasado"


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        Index("ix_expenses_user_month", "user_id", "mes_referencia"),  # CR-002: indice composto
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # CR-002: FK para isolamento de dados (RN-015)
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    parcela_atual: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parcela_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorrente: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=ExpenseStatus.PENDENTE.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    user = relationship("User", back_populates="expenses")  # CR-002
```

**Backend — Schemas (`backend/app/schemas.py` — secao Expense):**

> **Nota (CR-002):** Os schemas de input (`ExpenseCreate`, `ExpenseUpdate`) nao incluem `user_id` — ele e setado pelo router a partir do usuario autenticado (`current_user.id`). Os schemas permanecem inalterados.

```python
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from typing import Optional

from app.models import ExpenseStatus


class ExpenseCreate(BaseModel):
    """Schema para criacao de despesa. mes_referencia vem da URL, status padrao Pendente. user_id setado pelo router (CR-002)."""
    nome: str = Field(..., min_length=1, max_length=255)
    valor: float = Field(..., gt=0)
    vencimento: date
    parcela_atual: Optional[int] = Field(None, ge=1)
    parcela_total: Optional[int] = Field(None, ge=1)
    recorrente: bool = True
    subcategoria: Optional[str] = Field(None, max_length=50)  # CR-016

    @model_validator(mode="after")
    def validate_parcelas(self) -> "ExpenseCreate":
        """Regra de integridade do PRD: ambos os campos de parcela devem estar
        presentes ou ausentes, e parcela_atual <= parcela_total."""
        atual = self.parcela_atual
        total = self.parcela_total
        if (atual is None) != (total is None):
            raise ValueError(
                "parcela_atual e parcela_total devem ambos ser preenchidos ou ambos nulos"
            )
        if atual is not None and total is not None and atual > total:
            raise ValueError("parcela_atual deve ser <= parcela_total")
        return self


class ExpenseUpdate(BaseModel):
    """Schema para atualizacao parcial (PATCH). Apenas campos enviados sao alterados."""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    valor: Optional[float] = Field(None, gt=0)
    vencimento: Optional[date] = None
    parcela_atual: Optional[int] = Field(None, ge=1)
    parcela_total: Optional[int] = Field(None, ge=1)
    recorrente: Optional[bool] = None
    status: Optional[ExpenseStatus] = None
    subcategoria: Optional[str] = Field(None, max_length=50)  # CR-016


class ExpenseResponse(BaseModel):
    """Schema de resposta para despesa."""
    model_config = {"from_attributes": True}

    id: str
    mes_referencia: date
    nome: str
    categoria: Optional[str] = None  # CR-016
    subcategoria: Optional[str] = None  # CR-016
    valor: float
    vencimento: date
    parcela_atual: Optional[int]
    parcela_total: Optional[int]
    recorrente: bool
    status: str
    created_at: datetime
    updated_at: datetime
```

**Frontend — Types (`frontend/src/types.ts` — secao Expense):**

```typescript
export type ExpenseStatus = "Pendente" | "Pago" | "Atrasado";

export interface Expense {
  id: string;
  mes_referencia: string;
  nome: string;
  valor: number;
  vencimento: string;
  parcela_atual: number | null;
  parcela_total: number | null;
  recorrente: boolean;
  status: ExpenseStatus;
  created_at: string;
  updated_at: string;
}

export interface ExpenseCreate {
  nome: string;
  valor: number;
  vencimento: string;
  parcela_atual?: number | null;
  parcela_total?: number | null;
  recorrente: boolean;
}

export interface ExpenseUpdate {
  nome?: string;
  valor?: number;
  vencimento?: string;
  parcela_atual?: number | null;
  parcela_total?: number | null;
  recorrente?: boolean;
  status?: ExpenseStatus;
}
```

#### 2.4 Logica de Negocio

**CRUD — Camada de acesso a dados (`backend/app/crud.py` — secao Expenses):**

> **CR-002:** Funcoes de leitura agora recebem `user_id` para filtrar por usuario (RN-015). Funcoes de escrita (create/update/delete) nao recebem `user_id` — ownership e verificada pelo router antes de chamar.

```python
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date

from app.models import Expense, Income


# ========== Expenses ==========

def get_expenses_by_month(db: Session, mes_referencia: date, user_id: str) -> list[Expense]:
    """Retorna despesas de um usuario em um mes, ordenadas por vencimento. (CR-002: user_id)"""
    stmt = (
        select(Expense)
        .where(Expense.user_id == user_id, Expense.mes_referencia == mes_referencia)
        .order_by(Expense.vencimento)
    )
    return list(db.scalars(stmt).all())


def get_expense_by_id(db: Session, expense_id: str, user_id: str) -> Expense | None:
    """Retorna uma despesa por ID se pertence ao usuario, ou None. (CR-002: ownership check)"""
    stmt = (
        select(Expense)
        .where(Expense.id == expense_id, Expense.user_id == user_id)
    )
    return db.scalars(stmt).first()


def create_expense(db: Session, expense: Expense) -> Expense:
    """Persiste uma nova despesa. user_id ja deve estar setado na instancia."""
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def update_expense(db: Session, expense: Expense) -> Expense:
    """Persiste alteracoes em uma despesa existente."""
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: Expense) -> None:
    """Remove uma despesa."""
    db.delete(expense)
    db.commit()


def count_expenses_by_month(db: Session, mes_referencia: date, user_id: str) -> int:
    """Conta despesas do usuario no mes (check de idempotencia da transicao). (CR-002: user_id)"""
    stmt = (
        select(Expense)
        .where(Expense.user_id == user_id, Expense.mes_referencia == mes_referencia)
    )
    return len(list(db.scalars(stmt).all()))
```

**Criar Despesa:**
1. Receber `ExpenseCreate` do body + `year/month` do path
2. Construir `mes_referencia = date(year, month, 1)`
3. Criar instancia `Expense` com `status = "Pendente"`
4. Persistir via `crud.create_expense()`
5. Retornar `ExpenseResponse` (201)

**Atualizar Despesa (PATCH):**
1. Receber `expense_id` do path + `ExpenseUpdate` do body
2. Buscar despesa por ID — se nao existe: 404
3. Aplicar `model_dump(exclude_unset=True)` para obter apenas campos enviados
4. Para campo `status`: converter enum `.value` antes de `setattr`
5. Persistir via `crud.update_expense()`
6. Retornar `ExpenseResponse` atualizado

**Excluir Despesa (CR-009):**
1. Receber `expense_id` do path e `delete_all: bool = False` da query.
2. Buscar despesa por ID — se nao existe: 404.
3. Se `delete_all` for `True` e a despesa possuir parcelamento ou for marcada como recorrente: chamar func CRUD `delete_expense_related` que remove em massa via DB as despesas correspondentes daquele `user_id`.
4. Caso contrario, remover isoladamente via `crud.delete_expense()`.
5. Retornar 204 No Content.

#### 2.5 API Endpoints

**`backend/app/routers/expenses.py`** (CR-002: auth dependency + user scoping)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.auth import get_current_user  # CR-002
from app.models import Expense, ExpenseStatus, User  # CR-002: User
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app import crud

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.post("/{year}/{month}", response_model=ExpenseResponse, status_code=201)
def create_expense(
    year: int,
    month: int,
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """Criar nova despesa no mes especificado. user_id setado automaticamente."""
    mes_referencia = date(year, month, 1)
    expense = Expense(
        user_id=current_user.id,  # CR-002: isolamento de dados (RN-015)
        mes_referencia=mes_referencia,
        nome=data.nome,
        valor=data.valor,
        vencimento=data.vencimento,
        parcela_atual=data.parcela_atual,
        parcela_total=data.parcela_total,
        recorrente=data.recorrente,
        status=ExpenseStatus.PENDENTE.value,
    )
    return crud.create_expense(db, expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: str,
    data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """Atualizar despesa existente. PATCH: apenas campos enviados sao alterados."""
    expense = crud.get_expense_by_id(db, expense_id, current_user.id)  # CR-002: ownership check
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value is not None:
            setattr(expense, field, value.value)
        else:
            setattr(expense, field, value)

    return crud.update_expense(db, expense)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """Excluir despesa por ID."""
    expense = crud.get_expense_by_id(db, expense_id, current_user.id)  # CR-002: ownership check
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")
    crud.delete_expense(db, expense)
```

**Frontend — HTTP Client (`frontend/src/services/api.ts` — secao Expenses):**

> **CR-002:** A funcao `request()` agora inclui `Authorization: Bearer` automaticamente e trata respostas 401 tentando refresh do token.

```typescript
import type {
  MonthlySummary,
  ExpenseCreate,
  ExpenseUpdate,
  Expense,
  IncomeCreate,
  IncomeUpdate,
  Income,
} from "../types";

const BASE_URL = "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  // CR-002: incluir token de auth se disponivel
  const token = localStorage.getItem("access_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${url}`, {
    headers,
    ...options,
  });

  // CR-002: interceptar 401 para tentar refresh
  if (response.status === 401 && token) {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      try {
        const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (refreshResponse.ok) {
          const tokens = await refreshResponse.json();
          localStorage.setItem("access_token", tokens.access_token);
          localStorage.setItem("refresh_token", tokens.refresh_token);
          // Retry original request com novo token
          headers["Authorization"] = `Bearer ${tokens.access_token}`;
          const retryResponse = await fetch(`${BASE_URL}${url}`, {
            headers,
            ...options,
          });
          if (!retryResponse.ok) {
            const error = await retryResponse.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${retryResponse.status}`);
          }
          if (retryResponse.status === 204) return undefined as T;
          return retryResponse.json();
        }
      } catch {
        // Refresh falhou — limpar tokens e redirecionar
      }
    }
    // Refresh token invalido ou ausente
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
    throw new Error("Sessao expirada");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export function createExpense(
  year: number,
  month: number,
  data: ExpenseCreate
): Promise<Expense> {
  return request<Expense>(`/expenses/${year}/${month}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateExpense(
  id: string,
  data: ExpenseUpdate
): Promise<Expense> {
  return request<Expense>(`/expenses/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteExpense(id: string): Promise<void> {
  return request<void>(`/expenses/${id}`, { method: "DELETE" });
}
```

**Frontend — Hooks (`frontend/src/hooks/useExpenses.ts`):**

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../services/api";
import type { ExpenseCreate, ExpenseUpdate } from "../types";

function monthQueryKey(year: number, month: number) {
  return ["monthly-summary", year, month];
}

export function useCreateExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ExpenseCreate) => api.createExpense(year, month, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: monthQueryKey(year, month) });
    },
  });
}

export function useUpdateExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ExpenseUpdate }) =>
      api.updateExpense(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: monthQueryKey(year, month) });
    },
  });
}

export function useDeleteExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: monthQueryKey(year, month) });
    },
  });
}
```

#### 2.6 Validacoes

| Campo         | Regra                                              | Mensagem de Erro                                                  |
|---------------|----------------------------------------------------|--------------------------------------------------------------------|
| nome          | Obrigatorio, 1-255 chars                           | Validacao Pydantic Field                                           |
| valor         | Obrigatorio, > 0                                   | Validacao Pydantic Field(gt=0)                                     |
| vencimento    | Obrigatorio, tipo date                             | Validacao Pydantic                                                 |
| parcela_atual | Opcional, >= 1                                     | Validacao Pydantic Field(ge=1)                                     |
| parcela_total | Opcional, >= 1                                     | Validacao Pydantic Field(ge=1)                                     |
| parcelas      | Ambos presentes ou ambos nulos                     | "parcela_atual e parcela_total devem ambos ser preenchidos ou ambos nulos" |
| parcelas      | parcela_atual <= parcela_total                     | "parcela_atual deve ser <= parcela_total"                          |

---

### Feature: [RF-02] CRUD de Receitas

#### 2.1 Descricao Tecnica

Implementa criacao, leitura, edicao e exclusao de receitas mensais. Mesma estrutura de RF-01, porem mais simples (sem parcelas, sem status).

#### 2.2 Arquivos

| Acao  | Caminho                             | Descricao                              |
|-------|-------------------------------------|----------------------------------------|
| Criar | `backend/app/models.py`             | Modelo ORM Income (mesmo arquivo de Expense) |
| Criar | `backend/app/schemas.py`            | Schemas: IncomeCreate, IncomeUpdate, IncomeResponse |
| Criar | `backend/app/crud.py`               | Funcoes de acesso a dados para incomes |
| Criar | `backend/app/routers/incomes.py`    | Endpoints POST, PATCH, DELETE          |
| Criar | `frontend/src/types.ts`             | Types: Income, IncomeCreate, IncomeUpdate |
| Criar | `frontend/src/services/api.ts`      | Funcoes HTTP: createIncome, updateIncome, deleteIncome |
| Criar | `frontend/src/hooks/useIncomes.ts`  | Hooks TanStack Query para mutations    |

#### 2.3 Interfaces / Types

**Backend — Model (`backend/app/models.py` — secao Income):**

```python
class Income(Base):
    __tablename__ = "incomes"
    __table_args__ = (
        Index("ix_incomes_user_month", "user_id", "mes_referencia"),  # CR-002: indice composto
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # CR-002: FK para isolamento de dados (RN-015)
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    data: Mapped[date | None] = mapped_column(Date, nullable=True)
    recorrente: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    user = relationship("User", back_populates="incomes")  # CR-002
```

**Backend — Schemas (`backend/app/schemas.py` — secao Income):**

```python
class IncomeCreate(BaseModel):
    """Schema para criacao de receita."""
    nome: str = Field(..., min_length=1, max_length=255)
    valor: float = Field(..., gt=0)
    data: Optional[date] = None
    recorrente: bool = True


class IncomeUpdate(BaseModel):
    """Schema para atualizacao parcial de receita."""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    valor: Optional[float] = Field(None, gt=0)
    data: Optional[date] = None
    recorrente: Optional[bool] = None


class IncomeResponse(BaseModel):
    """Schema de resposta para receita."""
    model_config = {"from_attributes": True}

    id: str
    mes_referencia: date
    nome: str
    valor: float
    data: Optional[date]
    recorrente: bool
    created_at: datetime
    updated_at: datetime
```

**Frontend — Types (`frontend/src/types.ts` — secao Income):**

```typescript
export interface Income {
  id: string;
  mes_referencia: string;
  nome: string;
  valor: number;
  data: string | null;
  recorrente: boolean;
  created_at: string;
  updated_at: string;
}

export interface IncomeCreate {
  nome: string;
  valor: number;
  data?: string | null;
  recorrente: boolean;
}

export interface IncomeUpdate {
  nome?: string;
  valor?: number;
  data?: string | null;
  recorrente?: boolean;
}
```

#### 2.4 Logica de Negocio

**CRUD — Camada de acesso a dados (`backend/app/crud.py` — secao Incomes):**

```python
# ========== Incomes ==========

def get_incomes_by_month(db: Session, mes_referencia: date, user_id: str) -> list[Income]:
    """Retorna receitas de um usuario em um mes, ordenadas por data. (CR-002: user_id)"""
    stmt = (
        select(Income)
        .where(Income.user_id == user_id, Income.mes_referencia == mes_referencia)
        .order_by(Income.data)
    )
    return list(db.scalars(stmt).all())


def get_income_by_id(db: Session, income_id: str, user_id: str) -> Income | None:
    """Retorna uma receita por ID se pertence ao usuario, ou None. (CR-002: ownership check)"""
    stmt = (
        select(Income)
        .where(Income.id == income_id, Income.user_id == user_id)
    )
    return db.scalars(stmt).first()


def create_income(db: Session, income: Income) -> Income:
    """Persiste uma nova receita. user_id ja deve estar setado na instancia."""
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def update_income(db: Session, income: Income) -> Income:
    """Persiste alteracoes em uma receita existente."""
    db.commit()
    db.refresh(income)
    return income


def delete_income(db: Session, income: Income) -> None:
    """Remove uma receita."""
    db.delete(income)
    db.commit()
```

#### 2.5 API Endpoints

**`backend/app/routers/incomes.py`** (CR-002: auth dependency + user scoping)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.auth import get_current_user  # CR-002
from app.models import Income, User  # CR-002: User
from app.schemas import IncomeCreate, IncomeUpdate, IncomeResponse
from app import crud

router = APIRouter(prefix="/api/incomes", tags=["incomes"])


@router.post("/{year}/{month}", response_model=IncomeResponse, status_code=201)
def create_income(
    year: int,
    month: int,
    data: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """Criar nova receita no mes especificado. user_id setado automaticamente."""
    mes_referencia = date(year, month, 1)
    income = Income(
        user_id=current_user.id,  # CR-002: isolamento de dados (RN-015)
        mes_referencia=mes_referencia,
        nome=data.nome,
        valor=data.valor,
        data=data.data,
        recorrente=data.recorrente,
    )
    return crud.create_income(db, income)


@router.patch("/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: str,
    data: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """Atualizar receita existente."""
    income = crud.get_income_by_id(db, income_id, current_user.id)  # CR-002: ownership check
    if not income:
        raise HTTPException(status_code=404, detail="Receita nao encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(income, field, value)

    return crud.update_income(db, income)


@router.delete("/{income_id}", status_code=204)
def delete_income(
    income_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """Excluir receita por ID."""
    income = crud.get_income_by_id(db, income_id, current_user.id)  # CR-002: ownership check
    if not income:
        raise HTTPException(status_code=404, detail="Receita nao encontrada")
    crud.delete_income(db, income)
```

**Frontend — HTTP Client (`frontend/src/services/api.ts` — secao Incomes):**

```typescript
export function createIncome(
  year: number,
  month: number,
  data: IncomeCreate
): Promise<Income> {
  return request<Income>(`/incomes/${year}/${month}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateIncome(
  id: string,
  data: IncomeUpdate
): Promise<Income> {
  return request<Income>(`/incomes/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteIncome(id: string): Promise<void> {
  return request<void>(`/incomes/${id}`, { method: "DELETE" });
}
```

**Frontend — Hooks (`frontend/src/hooks/useIncomes.ts`):**

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../services/api";
import type { IncomeCreate, IncomeUpdate } from "../types";

function monthQueryKey(year: number, month: number) {
  return ["monthly-summary", year, month];
}

export function useCreateIncome(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: IncomeCreate) => api.createIncome(year, month, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: monthQueryKey(year, month) });
    },
  });
}

export function useUpdateIncome(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: IncomeUpdate }) =>
      api.updateIncome(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: monthQueryKey(year, month) });
    },
  });
}

export function useDeleteIncome(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteIncome(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: monthQueryKey(year, month) });
    },
  });
}
```

#### 2.6 Validacoes

| Campo | Regra                    | Mensagem de Erro               |
|-------|--------------------------|--------------------------------|
| nome  | Obrigatorio, 1-255 chars | Validacao Pydantic Field       |
| valor | Obrigatorio, > 0         | Validacao Pydantic Field(gt=0) |
| data  | Opcional, tipo date      | Validacao Pydantic             |

---

### Feature: [RF-03/RF-04] Visao Mensal e Totalizadores

#### 2.1 Descricao Tecnica

Endpoint principal que alimenta toda a pagina. Retorna despesas, receitas e totalizadores em uma unica chamada. Dispara automaticamente a geracao de mes (RF-06) e auto-deteccao de status (RF-05).

#### 2.2 Arquivos

| Acao  | Caminho                                    | Descricao                              |
|-------|--------------------------------------------|----------------------------------------|
| Criar | `backend/app/schemas.py`                   | Schema MonthlySummary                  |
| Criar | `backend/app/services.py`                  | Funcao get_monthly_summary             |
| Criar | `backend/app/routers/months.py`            | Endpoint GET /api/months/{year}/{month}|
| Criar | `frontend/src/types.ts`                    | Type MonthlySummary                    |
| Criar | `frontend/src/services/api.ts`             | Funcao fetchMonthlySummary             |
| Criar | `frontend/src/hooks/useMonthTransition.ts` | Hook useMonthlyView                    |
| Criar | `frontend/src/utils/format.ts`             | Formatacao BRL, parcela, data          |
| Criar | `frontend/src/utils/date.ts`               | Navegacao entre meses                  |

#### 2.3 Interfaces / Types

**Backend — Schema (`backend/app/schemas.py` — secao Summary):**

```python
class MonthlySummary(BaseModel):
    """Resposta composta da visao mensal: despesas + receitas + totalizadores."""
    mes_referencia: date
    total_despesas: float
    total_receitas: float
    saldo_livre: float
    total_pago: float       # CR-004: total despesas com status Pago
    total_pendente: float   # CR-004: total despesas com status Pendente
    total_atrasado: float   # CR-004: total despesas com status Atrasado
    expenses: list[ExpenseResponse]
    incomes: list[IncomeResponse]
```

**Invariante (CR-004):** `total_pago + total_pendente + total_atrasado == total_despesas` (sempre).

**Frontend — Type (`frontend/src/types.ts` — secao Summary):**

```typescript
export interface MonthlySummary {
  mes_referencia: string;
  total_despesas: number;
  total_receitas: number;
  saldo_livre: number;
  total_pago: number;       // CR-004
  total_pendente: number;   // CR-004
  total_atrasado: number;   // CR-004
  expenses: Expense[];
  incomes: Income[];
}
```

#### 2.4 Logica de Negocio

**`backend/app/services.py` — get_monthly_summary:** (CR-002: user_id propagado)

```python
def get_monthly_summary(db: Session, mes_referencia: date, user_id: str) -> dict:
    """
    Constroi a visao mensal completa para um usuario especifico. (CR-002: user_id)
    Passos:
    1. Tenta gerar dados do mes se vazio (RF-06)
    2. Busca despesas e receitas do usuario
    3. Aplica auto-deteccao de status (RF-05)
    4. Calcula totalizadores (RF-04)
    5. Calcula totalizadores por status (CR-004)
    """
    # Passo 1: Auto-gerar se necessario (escopo por usuario)
    generate_month_data(db, mes_referencia, user_id)  # CR-002

    # Passo 2: Buscar dados do usuario
    expenses = crud.get_expenses_by_month(db, mes_referencia, user_id)  # CR-002
    incomes = crud.get_incomes_by_month(db, mes_referencia, user_id)  # CR-002

    # Passo 3: Auto-detectar status de atraso
    today = date.today()
    apply_status_auto_detection(expenses, today)
    db.commit()  # Persiste mudancas de status

    # Passo 4: Calcular totalizadores
    total_despesas = sum(float(e.valor) for e in expenses)
    total_receitas = sum(float(i.valor) for i in incomes)

    # Passo 5: Totalizadores por status (CR-004)
    total_pago = sum(float(e.valor) for e in expenses if e.status == ExpenseStatus.PAGO.value)
    total_pendente = sum(float(e.valor) for e in expenses if e.status == ExpenseStatus.PENDENTE.value)
    total_atrasado = sum(float(e.valor) for e in expenses if e.status == ExpenseStatus.ATRASADO.value)

    return {
        "mes_referencia": mes_referencia,
        "total_despesas": round(total_despesas, 2),
        "total_receitas": round(total_receitas, 2),
        "saldo_livre": round(total_receitas - total_despesas, 2),
        "total_pago": round(total_pago, 2),          # CR-004
        "total_pendente": round(total_pendente, 2),    # CR-004
        "total_atrasado": round(total_atrasado, 2),    # CR-004
        "expenses": expenses,
        "incomes": incomes,
    }
```

#### 2.5 API Endpoints

**`backend/app/routers/months.py`** (CR-002: auth dependency + user scoping)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.auth import get_current_user  # CR-002
from app.models import User  # CR-002
from app.schemas import MonthlySummary
from app import services

router = APIRouter(prefix="/api/months", tags=["months"])


@router.get("/{year}/{month}", response_model=MonthlySummary)
def get_monthly_view(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """
    GET /api/months/2026/2 → visao mensal completa de fevereiro 2026.
    Dispara geracao de mes se vazio (RF-06).
    Aplica auto-deteccao de status (RF-05).
    Retorna despesas, receitas e totalizadores.
    Dados filtrados por usuario autenticado (CR-002, RN-015).
    """
    mes_referencia = date(year, month, 1)
    summary = services.get_monthly_summary(db, mes_referencia, current_user.id)  # CR-002
    return summary
```

**Frontend — HTTP Client:**

```typescript
export function fetchMonthlySummary(
  year: number,
  month: number
): Promise<MonthlySummary> {
  return request<MonthlySummary>(`/months/${year}/${month}`);
}
```

**Frontend — Hook (`frontend/src/hooks/useMonthTransition.ts`):**

```typescript
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchMonthlySummary } from "../services/api";
import {
  getCurrentMonthRef,
  getNextMonth,
  getPreviousMonth,
} from "../utils/date";
import type { MonthlySummary } from "../types";

export function useMonthlyView() {
  const [monthRef, setMonthRef] = useState(getCurrentMonthRef);

  const query = useQuery<MonthlySummary>({
    queryKey: ["monthly-summary", monthRef.year, monthRef.month],
    queryFn: () => fetchMonthlySummary(monthRef.year, monthRef.month),
  });

  function goToPreviousMonth() {
    setMonthRef((prev) => getPreviousMonth(prev.year, prev.month));
  }

  function goToNextMonth() {
    setMonthRef((prev) => getNextMonth(prev.year, prev.month));
  }

  return {
    year: monthRef.year,
    month: monthRef.month,
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    goToPreviousMonth,
    goToNextMonth,
  };
}
```

**Frontend — Utilitarios (`frontend/src/utils/format.ts`):**

```typescript
const brlFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

/** Formata numero como moeda brasileira: R$ 1.234,56 */
export function formatBRL(value: number): string {
  return brlFormatter.format(value);
}

/** Formata parcela como "X de Y" ou string vazia se nao aplicavel */
export function formatParcela(
  atual: number | null,
  total: number | null
): string {
  if (atual === null || total === null) return "";
  return `${atual} de ${total}`;
}

/** Formata data ISO (YYYY-MM-DD) para DD/MM */
export function formatDateBR(isoDate: string | null): string {
  if (!isoDate) return "";
  const [, month, day] = isoDate.split("-");
  return `${day}/${month}`;
}
```

**Frontend — Utilitarios (`frontend/src/utils/date.ts`):**

```typescript
const MONTH_NAMES = [
  "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

export function getCurrentMonthRef(): { year: number; month: number } {
  const now = new Date();
  return { year: now.getFullYear(), month: now.getMonth() + 1 };
}

export function getMonthName(month: number): string {
  return MONTH_NAMES[month - 1];
}

export function getMonthLabel(year: number, month: number): string {
  return `${getMonthName(month)} ${year}`;
}

export function getPreviousMonth(
  year: number,
  month: number
): { year: number; month: number } {
  if (month === 1) return { year: year - 1, month: 12 };
  return { year, month: month - 1 };
}

export function getNextMonth(
  year: number,
  month: number
): { year: number; month: number } {
  if (month === 12) return { year: year + 1, month: 1 };
  return { year, month: month + 1 };
}
```

---

### Feature: [RF-05] Gestao de Status

#### 2.1 Descricao Tecnica

Auto-deteccao de atraso no servidor e toggle de status via UI. Despesas com vencimento passado e status "Pendente" sao automaticamente marcadas como "Atrasado". O usuario pode alternar entre Pendente e Pago clicando no badge de status.

#### 2.2 Arquivos

| Acao  | Caminho                    | Descricao                              |
|-------|----------------------------|----------------------------------------|
| Criar | `backend/app/services.py`  | Funcao apply_status_auto_detection     |
| Usar  | `backend/app/routers/expenses.py` | PATCH para toggle de status     |
| Usar  | `frontend/src/hooks/useExpenses.ts` | useUpdateExpense para status  |

#### 2.3 Logica de Negocio

**`backend/app/services.py` — apply_status_auto_detection:**

```python
def apply_status_auto_detection(
    expenses: list[Expense], today: date
) -> list[Expense]:
    """
    RF-05: Para despesas com status "Pendente" e vencimento < hoje,
    marca como "Atrasado". Modifica as instancias in-place.
    O chamador decide se persiste as mudancas.
    """
    for expense in expenses:
        if (
            expense.status == ExpenseStatus.PENDENTE.value
            and expense.vencimento < today
        ):
            expense.status = ExpenseStatus.ATRASADO.value
    return expenses
```

**Toggle de status na UI:**
- Clicar em `Pendente` → muda para `Pago` (via PATCH `{ "status": "Pago" }`)
- Clicar em `Atrasado` → muda para `Pago` (usuario pagou despesa atrasada)
- Clicar em `Pago` → muda para `Pendente` (via PATCH `{ "status": "Pendente" }`)

---

### Feature: [RF-06] Transicao Automatica de Mes

#### 2.1 Descricao Tecnica

Algoritmo mais complexo do sistema. Quando o usuario navega para um mes sem dados, gera automaticamente lancamentos a partir do mes anterior seguindo regras de replicacao para despesas recorrentes, parceladas e receitas.

#### 2.2 Arquivos

| Acao  | Caminho                   | Descricao                              |
|-------|---------------------------|----------------------------------------|
| Criar | `backend/app/services.py` | generate_month_data, helpers de data   |

#### 2.3 Logica de Negocio

**`backend/app/services.py` — Funcoes auxiliares + Algoritmo de Transicao:**

```python
import calendar
from datetime import date

from sqlalchemy.orm import Session

from app import crud
from app.models import Expense, ExpenseStatus, Income


def get_next_month(current: date) -> date:
    """Dado um mes_referencia (1o dia do mes), retorna 1o dia do proximo mes."""
    if current.month == 12:
        return date(current.year + 1, 1, 1)
    return date(current.year, current.month + 1, 1)


def get_previous_month(current: date) -> date:
    """Dado um mes_referencia (1o dia do mes), retorna 1o dia do mes anterior."""
    if current.month == 1:
        return date(current.year - 1, 12, 1)
    return date(current.year, current.month - 1, 1)


def adjust_vencimento_to_month(original_date: date, target_mes: date) -> date:
    """
    Move uma data para o mes-alvo mantendo o mesmo dia.
    Se o dia nao existe no mes-alvo (ex: 31 jan -> fev), clamp para o ultimo dia.
    """
    last_day = calendar.monthrange(target_mes.year, target_mes.month)[1]
    day = min(original_date.day, last_day)
    return date(target_mes.year, target_mes.month, day)


def generate_month_data(db: Session, target_mes: date, user_id: str) -> bool:
    """
    RF-06: Algoritmo de Transicao de Mes. (CR-002: user_id para isolamento)

    Chamado quando o usuario navega para um mes sem dados.
    Olha os dados do mes anterior DO MESMO USUARIO e gera entradas para target_mes
    seguindo as regras de replicacao.

    Retorna True se dados foram gerados, False se o mes-alvo ja tinha dados
    ou o mes anterior nao tinha dados (nada a replicar).

    Algoritmo:
    1. Checar se target_mes ja tem dados do usuario → se sim, return False (idempotente)
    2. Buscar despesas e receitas do usuario no mes anterior
    3. Para cada despesa:
       a. Tem parcela (parcela_atual e parcela_total preenchidos)?
          - Se parcela_atual < parcela_total: replicar com parcela_atual + 1
          - Se parcela_atual == parcela_total: NAO replicar (ultima parcela)
       b. Nao tem parcela?
          - Se recorrente == True: replicar com mesmos dados
          - Se recorrente == False: NAO replicar (despesa avulsa)
    4. Para cada receita:
       - Se recorrente == True: replicar
       - Se recorrente == False: NAO replicar
    5. Todas as novas entradas recebem status = Pendente, novos UUIDs e user_id do usuario.
    """
    # Passo 1: Check de idempotencia (escopo por usuario)
    existing_expenses = crud.count_expenses_by_month(db, target_mes, user_id)  # CR-002
    existing_incomes = len(crud.get_incomes_by_month(db, target_mes, user_id))  # CR-002
    if existing_expenses > 0 or existing_incomes > 0:
        return False

    # Passo 2: Buscar dados do usuario no mes anterior
    prev_mes = get_previous_month(target_mes)
    prev_expenses = crud.get_expenses_by_month(db, prev_mes, user_id)  # CR-002
    prev_incomes = crud.get_incomes_by_month(db, prev_mes, user_id)  # CR-002

    if not prev_expenses and not prev_incomes:
        return False

    # Passo 3: Replicar despesas
    for exp in prev_expenses:
        if exp.parcela_atual is not None and exp.parcela_total is not None:
            # Despesa parcelada
            if exp.parcela_atual < exp.parcela_total:
                new_exp = Expense(
                    user_id=user_id,  # CR-002
                    mes_referencia=target_mes,
                    nome=exp.nome,
                    valor=exp.valor,
                    vencimento=adjust_vencimento_to_month(
                        exp.vencimento, target_mes
                    ),
                    parcela_atual=exp.parcela_atual + 1,
                    parcela_total=exp.parcela_total,
                    recorrente=exp.recorrente,
                    status=ExpenseStatus.PENDENTE.value,
                )
                db.add(new_exp)
            # else: ultima parcela, NAO replica
        else:
            # Despesa sem parcela
            if exp.recorrente:
                new_exp = Expense(
                    user_id=user_id,  # CR-002
                    mes_referencia=target_mes,
                    nome=exp.nome,
                    valor=exp.valor,
                    vencimento=adjust_vencimento_to_month(
                        exp.vencimento, target_mes
                    ),
                    parcela_atual=None,
                    parcela_total=None,
                    recorrente=True,
                    status=ExpenseStatus.PENDENTE.value,
                )
                db.add(new_exp)
            # else: nao recorrente, NAO replica

    # Passo 4: Replicar receitas
    for inc in prev_incomes:
        if inc.recorrente:
            new_inc = Income(
                user_id=user_id,  # CR-002
                mes_referencia=target_mes,
                nome=inc.nome,
                valor=inc.valor,
                data=(
                    adjust_vencimento_to_month(inc.data, target_mes)
                    if inc.data
                    else None
                ),
                recorrente=True,
            )
            db.add(new_inc)
        # else: nao recorrente, NAO replica

    db.commit()
    return True
```

---

### Feature: [RF-07] Cadastro Rapido (Duplicar)

#### 2.1 Descricao Tecnica

Permite duplicar uma despesa existente no mesmo mes, copiando todos os campos e resetando o status para "Pendente" com novo UUID.

#### 2.2 Arquivos

| Acao  | Caminho                              | Descricao                 |
|-------|--------------------------------------|---------------------------|
| Usar  | `backend/app/routers/expenses.py`    | Endpoint POST /duplicate  |
| Criar | `frontend/src/services/api.ts`       | Funcao duplicateExpense   |
| Criar | `frontend/src/hooks/useExpenses.ts`  | Hook useDuplicateExpense  |

#### 2.3 Codigo

**Backend — Endpoint de duplicacao (em `routers/expenses.py`):** (CR-002: auth + user_id)

```python
@router.post(
    "/{expense_id}/duplicate", response_model=ExpenseResponse, status_code=201
)
def duplicate_expense(
    expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """RF-07: Duplicar despesa existente no mesmo mes."""
    original = crud.get_expense_by_id(db, expense_id, current_user.id)  # CR-002: ownership check
    if not original:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")

    new_expense = Expense(
        user_id=current_user.id,  # CR-002: isolamento de dados
        mes_referencia=original.mes_referencia,
        nome=original.nome,
        valor=original.valor,
        vencimento=original.vencimento,
        parcela_atual=original.parcela_atual,
        parcela_total=original.parcela_total,
        recorrente=original.recorrente,
        status=ExpenseStatus.PENDENTE.value,
    )
    return crud.create_expense(db, new_expense)
```

**Frontend — HTTP + Hook:**

```typescript
// api.ts
export function duplicateExpense(id: string): Promise<Expense> {
  return request<Expense>(`/expenses/${id}/duplicate`, { method: "POST" });
}

// useExpenses.ts
export function useDuplicateExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.duplicateExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: monthQueryKey(year, month) });
    },
  });
}
```

---

### Feature: [RF-13] Gastos Diarios (CR-005)

#### 2.1 Descricao Tecnica

CRUD de gastos diarios nao planejados com categorias fixas (14 + Outros), visao mensal agrupada por dia e navegacao via ViewSelector. A categoria e auto-derivada da subcategoria escolhida pelo usuario. Gastos diarios sao completamente independentes dos gastos planejados — nao participam da transicao automatica de mes e tem modelo de dados proprio (`DailyExpense`).

#### 2.2 Arquivos

**Novos:**

| Acao  | Caminho                                           | Descricao                                       |
|-------|---------------------------------------------------|-------------------------------------------------|
| Criar | `backend/app/categories.py`                       | Categorias fixas + metodos pagamento + helpers  |
| Criar | `backend/alembic/versions/004_add_daily_expenses.py` | Migration: cria tabela daily_expenses         |
| Criar | `backend/app/routers/daily_expenses.py`           | Router com 5 endpoints                          |
| Criar | `frontend/src/hooks/useDailyExpenses.ts`          | 5 hooks TanStack Query                          |
| Criar | `frontend/src/hooks/useDailyExpensesView.ts`      | Hook navegacao mensal                           |
| Criar | `frontend/src/components/DailyExpenseTable.tsx`    | Tabela agrupada por dia                         |
| Criar | `frontend/src/components/DailyExpenseFormModal.tsx`| Modal formulario gasto diario                   |
| Criar | `frontend/src/components/ViewSelector.tsx`         | Seletor Planejados/Diarios                      |
| Criar | `frontend/src/pages/DailyExpensesView.tsx`         | Pagina principal gastos diarios                 |

**Modificados:**

| Acao      | Caminho                              | Descricao                                       |
|-----------|--------------------------------------|-------------------------------------------------|
| Atualizar | `backend/app/models.py`              | +DailyExpense model, +User.daily_expenses rel   |
| Atualizar | `backend/app/schemas.py`             | +6 schemas Pydantic                             |
| Atualizar | `backend/app/crud.py`                | +5 funcoes CRUD                                 |
| Atualizar | `backend/app/services.py`            | +get_daily_expenses_monthly_summary()           |
| Atualizar | `backend/app/main.py`                | +include_router(daily_expenses)                 |
| Atualizar | `frontend/src/types.ts`              | +6 interfaces TypeScript                        |
| Atualizar | `frontend/src/services/api.ts`       | +5 funcoes API                                  |
| Atualizar | `frontend/src/utils/format.ts`       | +formatDateFull()                               |
| Atualizar | `frontend/src/App.tsx`               | +rota /daily-expenses                           |
| Atualizar | `frontend/src/pages/MonthlyView.tsx`  | +ViewSelector no topo                           |

#### 2.3 Codigo

**`backend/app/categories.py` — Categorias e Metodos de Pagamento:**

```python
DAILY_EXPENSE_CATEGORIES = {
    "Alimentacao": ["Supermercado", "Feira/Sacolao", "Acougue/Peixaria", "Padaria", "Restaurante/Lanchonete", "Delivery/App de Comida", "Cafeteria", "Loja de Conveniencia", "Outros Alimentacao"],
    "Transporte": ["Combustivel", "Estacionamento", "Pedagio", "Transporte Publico", "Aplicativo de Transporte", "Manutencao Veiculo", "Lavagem Veiculo", "Outros Transporte"],
    "Saude": ["Farmacia", "Consulta Medica", "Exames", "Dentista", "Otica", "Outros Saude"],
    "Higiene e Beleza": ["Cabeleireiro/Barbearia", "Produtos de Higiene", "Cosmeticos", "Outros Higiene"],
    "Casa e Manutencao": ["Material de Limpeza", "Manutencao Residencial", "Utensilios Domesticos", "Decoracao", "Outros Casa"],
    "Educacao": ["Material Escolar", "Livros", "Cursos Extras", "Outros Educacao"],
    "Lazer e Entretenimento": ["Cinema/Teatro", "Streaming/Assinatura", "Jogos", "Passeios/Viagens", "Hobbies", "Outros Lazer"],
    "Vestuario": ["Roupas", "Calcados", "Acessorios", "Outros Vestuario"],
    "Pet": ["Racao/Petiscos", "Veterinario", "Acessorios Pet", "Banho/Tosa", "Outros Pet"],
    "Presentes e Doacoes": ["Presentes", "Doacoes", "Outros Presentes"],
    "Tecnologia": ["Eletronicos", "Acessorios Tech", "Apps/Software", "Outros Tecnologia"],
    "Servicos": ["Correios/Entregas", "Cartorio", "Impressao/Xerox", "Chaveiro/Reparos", "Outros Servicos"],
    "Filhos/Dependentes": ["Escola/Creche Extras", "Brinquedos", "Roupas Infantis", "Atividades Extracurriculares", "Outros Filhos"],
    "Impostos e Taxas": ["IPVA", "IPTU", "Multas", "Taxas Diversas", "Outros Impostos"],
    "Outros": ["Outros"],
}

PAYMENT_METHODS = [
    "Dinheiro", "Cartao de Credito", "Cartao de Debito",
    "Pix", "Vale Alimentacao", "Vale Refeicao",
]

def get_category_for_subcategory(subcategoria: str) -> str | None:
    """Retorna a categoria pai de uma subcategoria."""
    for cat, subs in DAILY_EXPENSE_CATEGORIES.items():
        if subcategoria in subs:
            return cat
    return None

def is_valid_subcategory(subcategoria: str) -> bool:
    return get_category_for_subcategory(subcategoria) is not None

def is_valid_payment_method(metodo: str) -> bool:
    return metodo in PAYMENT_METHODS
```

**Schemas (em `schemas.py`):**

```python
class DailyExpenseCreate(BaseModel):
    descricao: str = Field(min_length=1, max_length=255)
    valor: float = Field(gt=0)
    data: date
    subcategoria: str = Field(min_length=1, max_length=50)
    metodo_pagamento: str = Field(min_length=1, max_length=30)

class DailyExpenseUpdate(BaseModel):
    descricao: str | None = Field(None, min_length=1, max_length=255)
    valor: float | None = Field(None, gt=0)
    data: date | None = None
    subcategoria: str | None = Field(None, min_length=1, max_length=50)
    metodo_pagamento: str | None = Field(None, min_length=1, max_length=30)

class DailyExpenseResponse(BaseModel):
    id: str
    user_id: str
    mes_referencia: date
    descricao: str
    valor: float
    data: date
    categoria: str
    subcategoria: str
    metodo_pagamento: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DailyExpenseDaySummary(BaseModel):
    data: str
    gastos: list[DailyExpenseResponse]
    subtotal: float

class DailyExpenseMonthlySummary(BaseModel):
    mes_referencia: date
    total_mes: float
    dias: list[DailyExpenseDaySummary]

class CategoriesResponse(BaseModel):
    categorias: dict[str, list[str]]
    metodos_pagamento: list[str]
```

**Router (`backend/app/routers/daily_expenses.py`):**

```python
router = APIRouter(prefix="/api/daily-expenses", tags=["daily-expenses"])

@router.get("/categories", response_model=CategoriesResponse)
def get_categories():
    """Retorna categorias e metodos de pagamento (publico)."""

@router.get("/{year}/{month}", response_model=DailyExpenseMonthlySummary)
def get_monthly_daily_expenses(year: int, month: int, db, current_user):
    """Visao mensal agrupada por dia."""

@router.post("/{year}/{month}", response_model=DailyExpenseResponse, status_code=201)
def create_daily_expense(year: int, month: int, data: DailyExpenseCreate, db, current_user):
    """Criar gasto diario. Valida subcategoria e metodo_pagamento. Auto-deriva categoria."""

@router.patch("/{daily_expense_id}", response_model=DailyExpenseResponse)
def update_daily_expense(daily_expense_id: str, data: DailyExpenseUpdate, db, current_user):
    """Atualizar gasto diario. Ownership check + validacao."""

@router.delete("/{daily_expense_id}", status_code=204)
def delete_daily_expense(daily_expense_id: str, db, current_user):
    """Excluir gasto diario. Ownership check."""
```

**Frontend — Tipos (em `types.ts`):**

```typescript
export interface DailyExpense {
  id: string; user_id: string; mes_referencia: string;
  descricao: string; valor: number; data: string;
  categoria: string; subcategoria: string; metodo_pagamento: string;
  created_at: string; updated_at: string;
}
export interface DailyExpenseCreate {
  descricao: string; valor: number; data: string;
  subcategoria: string; metodo_pagamento: string;
}
export interface DailyExpenseUpdate { /* todos opcionais */ }
export interface DailyExpenseDaySummary {
  data: string; gastos: DailyExpense[]; subtotal: number;
}
export interface DailyExpenseMonthlySummary {
  mes_referencia: string; total_mes: number; dias: DailyExpenseDaySummary[];
}
export interface CategoriesData {
  categorias: Record<string, string[]>; metodos_pagamento: string[];
}
```

**Frontend — Hooks (em `useDailyExpenses.ts`):**

- `useDailyExpensesMonthly(year, month)` — query key `["daily-expenses-summary", year, month]`
- `useDailyExpensesCategories()` — query key `["daily-expenses-categories"]`, staleTime: Infinity
- `useCreateDailyExpense(year, month)` — invalida `["daily-expenses-summary"]`
- `useUpdateDailyExpense()` — invalida `["daily-expenses-summary"]`
- `useDeleteDailyExpense()` — invalida `["daily-expenses-summary"]`

**Frontend — Componentes:**

- `ViewSelector.tsx` — Pills/tabs usando `useNavigate` e `useLocation`. Alterna entre `/` (Gastos Planejados), `/daily-expenses` (Gastos Diarios) e `/installments` (Parcelas). Integrado no topo de `MonthlyView`, `DailyExpensesView` e `InstallmentsView`. Responsivo: padding compacto em mobile (`px-3 sm:px-5`), font menor (`text-xs sm:text-sm`), `overflow-x-auto` e `whitespace-nowrap` para seguranca (CR-012).
- `DailyExpenseFormModal.tsx` — Modal com 5 campos: descricao, valor, data (default=hoje), categoria+subcategoria (selects cascateados), metodo_pagamento (select). Suporta criacao e edicao via prop `initialData`.
- `DailyExpenseTable.tsx` — Tabela agrupada por dia com sub-componente `DayGroup`. Header do dia com data formatada (`formatDateFull`) + subtotal. Rows com descricao, valor, subcategoria (badge), metodo_pagamento, acoes (Editar/Excluir). Footer com "Total do Mes". Estado vazio com mensagem. Responsivo: padding `px-3 sm:px-6` em cells, botoes de acao compactos em mobile (`px-1.5 sm:px-2.5`), header compacto (`px-3 py-3 sm:px-6 sm:py-4`) (CR-012).
- `DailyExpensesView.tsx` — Pagina principal: ViewSelector + MonthNavigator + DailyExpenseTable. Loading/error states.

**Frontend — Utilidade (em `format.ts`):**

```typescript
export function formatDateFull(dateStr: string): string {
  const [year, month, day] = dateStr.split("-").map(Number);
  const date = new Date(year, month - 1, day);
  const dd = String(day).padStart(2, "0");
  const mm = String(month).padStart(2, "0");
  const weekday = date.toLocaleDateString("pt-BR", { weekday: "long" });
  const capitalized = weekday.charAt(0).toUpperCase() + weekday.slice(1);
  return `${dd}/${mm} - ${capitalized}`;
}
```

---

