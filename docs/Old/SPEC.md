# SPEC — Meu Controle (Fase 1)

**Versao:** 1.0
**Data:** 2026-02-06
**Base:** PRD_MeuControle.md v1.0

---

## 1. Visao Geral da Arquitetura

| Camada        | Tecnologia                          |
|---------------|-------------------------------------|
| Frontend      | React 19 + TypeScript + Vite 6      |
| Estilizacao   | Tailwind CSS v4 (plugin Vite)       |
| State/Fetch   | TanStack Query v5                   |
| HTTP Client   | fetch nativo                        |
| Backend       | Python + FastAPI                    |
| ORM           | SQLAlchemy 2.0+                     |
| Banco de Dados| SQLite (arquivo local)              |
| Arquitetura   | Monorepo (frontend/ + backend/)     |

**Decisoes-chave:**
- Sem axios (fetch nativo e suficiente e evita dependencia extra).
- Sem react-router (Fase 1 tem uma unica pagina).
- Sem Alembic (SQLAlchemy `create_all()` e suficiente para MVP single-user).
- SQLAlchemy sincrono (SQLite nao suporta async I/O real; async adicionaria complexidade sem beneficio).

---

## 2. Estrutura do Projeto

```
Personal Finance/
├── docs/
│   ├── PRD_MeuControle.md
│   └── SPEC.md
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── crud.py
│       ├── services.py
│       └── routers/
│           ├── __init__.py
│           ├── expenses.py
│           ├── incomes.py
│           └── months.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.app.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── types.ts
│       ├── utils/
│       │   ├── format.ts
│       │   └── date.ts
│       ├── services/
│       │   └── api.ts
│       ├── hooks/
│       │   ├── useExpenses.ts
│       │   ├── useIncomes.ts
│       │   └── useMonthTransition.ts
│       ├── components/
│       │   ├── MonthNavigator.tsx
│       │   ├── IncomeTable.tsx
│       │   ├── ExpenseTable.tsx
│       │   ├── SaldoLivre.tsx
│       │   ├── StatusBadge.tsx
│       │   ├── ExpenseFormModal.tsx
│       │   ├── IncomeFormModal.tsx
│       │   └── ConfirmDialog.tsx
│       └── pages/
│           └── MonthlyView.tsx
└── .gitignore
```

**Total: 35 arquivos** (incluindo `__init__.py`).

---

## 3. Contratos da API

| Metodo   | Path                                | Body             | Resposta                | Descricao                                      |
|----------|-------------------------------------|------------------|-------------------------|-------------------------------------------------|
| `GET`    | `/api/months/{year}/{month}`        | —                | `MonthlySummary`        | Visao mensal completa. Dispara RF-06 + RF-05.   |
| `POST`   | `/api/expenses/{year}/{month}`      | `ExpenseCreate`  | `ExpenseResponse` (201) | Criar despesa no mes                            |
| `PATCH`  | `/api/expenses/{expense_id}`        | `ExpenseUpdate`  | `ExpenseResponse`       | Atualizar campos da despesa                     |
| `DELETE` | `/api/expenses/{expense_id}`        | —                | 204 No Content          | Excluir despesa                                 |
| `POST`   | `/api/expenses/{expense_id}/duplicate` | —             | `ExpenseResponse` (201) | RF-07: Duplicar despesa                         |
| `POST`   | `/api/incomes/{year}/{month}`       | `IncomeCreate`   | `IncomeResponse` (201)  | Criar receita no mes                            |
| `PATCH`  | `/api/incomes/{income_id}`          | `IncomeUpdate`   | `IncomeResponse`        | Atualizar campos da receita                     |
| `DELETE` | `/api/incomes/{income_id}`          | —                | 204 No Content          | Excluir receita                                 |
| `GET`    | `/api/health`                       | —                | `{"status": "ok"}`      | Health check                                    |

**Nota:** O endpoint principal e `GET /api/months/{year}/{month}`. Ele retorna tudo que o frontend precisa em uma unica chamada: despesas, receitas e totalizadores. Tambem dispara a geracao automatica de mes (RF-06) e a auto-deteccao de status (RF-05).

---

## 4. Backend — Arquivos a Criar

### 4.1 `backend/requirements.txt`

**Responsabilidade:** Dependencias Python pinadas.

```
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy==2.0.*
pydantic==2.*
```

**Notas:**
- `uvicorn[standard]` inclui uvloop e httptools para melhor performance.
- Sem Alembic — `create_all()` e suficiente para Fase 1.

---

### 4.2 `backend/app/__init__.py`

**Responsabilidade:** Torna `app/` um pacote Python. Arquivo vazio.

---

### 4.3 `backend/app/database.py`

**Responsabilidade:** Engine SQLAlchemy, fabrica de sessoes, classe Base e dependency injection para FastAPI.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

DATABASE_URL = "sqlite:///meu_controle.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessario para SQLite com FastAPI
)

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

**Exports:** `engine`, `SessionLocal`, `Base`, `get_db`

**Decisoes:**
- SQLAlchemy sincrono. SQLite nao suporta async I/O real; usar async adicionaria complexidade sem ganho.
- `check_same_thread=False` e necessario porque FastAPI serve requests de multiplas threads, mas SQLite e single-writer. Seguro para app single-user.

---

### 4.4 `backend/app/models.py`

**Responsabilidade:** Modelos ORM SQLAlchemy para tabelas `expenses` e `incomes`.

```python
import uuid
import enum
from datetime import date, datetime

from sqlalchemy import String, Date, Boolean, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExpenseStatus(str, enum.Enum):
    PENDENTE = "Pendente"
    PAGO = "Pago"
    ATRASADO = "Atrasado"


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
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


class Income(Base):
    __tablename__ = "incomes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    data: Mapped[date | None] = mapped_column(Date, nullable=True)
    recorrente: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )
```

**Exports:** `ExpenseStatus`, `Expense`, `Income`

**Decisoes:**
- UUID armazenado como `String(36)` porque SQLite nao tem tipo UUID nativo.
- `status` como `String(20)` ao inves de SQLAlchemy `Enum` para evitar complicacoes com SQLite. Validacao feita na camada de aplicacao com o enum Python.
- `mes_referencia` indexado porque toda query filtra por essa coluna.
- `Numeric(10,2)` para valores monetarios evita problemas de precisao de float.
- `datetime.now` (nao `datetime.utcnow` que esta deprecado no Python 3.12+).

---

### 4.5 `backend/app/schemas.py`

**Responsabilidade:** Schemas Pydantic V2 para validacao de request/response e serializacao.

```python
from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from typing import Optional

from app.models import ExpenseStatus


# ========== Expense Schemas ==========

class ExpenseCreate(BaseModel):
    """Schema para criacao de despesa. mes_referencia vem da URL, status padrao Pendente."""
    nome: str = Field(..., min_length=1, max_length=255)
    valor: float = Field(..., gt=0)
    vencimento: date
    parcela_atual: Optional[int] = Field(None, ge=1)
    parcela_total: Optional[int] = Field(None, ge=1)
    recorrente: bool = True

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


class ExpenseResponse(BaseModel):
    """Schema de resposta para despesa."""
    model_config = {"from_attributes": True}

    id: str
    mes_referencia: date
    nome: str
    valor: float
    vencimento: date
    parcela_atual: Optional[int]
    parcela_total: Optional[int]
    recorrente: bool
    status: str
    created_at: datetime
    updated_at: datetime


# ========== Income Schemas ==========

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


# ========== Summary Schema ==========

class MonthlySummary(BaseModel):
    """Resposta composta da visao mensal: despesas + receitas + totalizadores."""
    mes_referencia: date
    total_despesas: float
    total_receitas: float
    saldo_livre: float
    expenses: list[ExpenseResponse]
    incomes: list[IncomeResponse]
```

**Exports:** Todos os schemas listados.

**Decisoes:**
- `ExpenseCreate` NAO inclui `mes_referencia` nem `status`. O `mes_referencia` vem do path parameter da URL. O `status` e sempre "Pendente" ao criar.
- `ExpenseUpdate` usa campos opcionais para semantica PATCH: apenas campos enviados sao atualizados.
- `MonthlySummary` agrupa despesas, receitas e totalizadores em uma unica resposta, evitando 3 chamadas separadas do frontend.
- O `model_validator` no `ExpenseCreate` implementa a regra de integridade do PRD: parcela_atual e parcela_total devem ambos estar presentes ou ambos ausentes, e parcela_atual <= parcela_total.

---

### 4.6 `backend/app/crud.py`

**Responsabilidade:** Funcoes puras de acesso a dados. Sem logica de negocio. Cada funcao recebe `Session` e retorna instancias de modelo SQLAlchemy.

```python
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date

from app.models import Expense, Income


# ========== Expenses ==========

def get_expenses_by_month(db: Session, mes_referencia: date) -> list[Expense]:
    """Retorna todas as despesas de um mes, ordenadas por vencimento."""
    stmt = (
        select(Expense)
        .where(Expense.mes_referencia == mes_referencia)
        .order_by(Expense.vencimento)
    )
    return list(db.scalars(stmt).all())


def get_expense_by_id(db: Session, expense_id: str) -> Expense | None:
    """Retorna uma despesa por ID ou None."""
    return db.get(Expense, expense_id)


def create_expense(db: Session, expense: Expense) -> Expense:
    """Persiste uma nova despesa."""
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


def count_expenses_by_month(db: Session, mes_referencia: date) -> int:
    """Conta despesas no mes (usado pelo check de idempotencia da transicao)."""
    stmt = select(Expense).where(Expense.mes_referencia == mes_referencia)
    return len(list(db.scalars(stmt).all()))


# ========== Incomes ==========

def get_incomes_by_month(db: Session, mes_referencia: date) -> list[Income]:
    """Retorna todas as receitas de um mes, ordenadas por data."""
    stmt = (
        select(Income)
        .where(Income.mes_referencia == mes_referencia)
        .order_by(Income.data)
    )
    return list(db.scalars(stmt).all())


def get_income_by_id(db: Session, income_id: str) -> Income | None:
    """Retorna uma receita por ID ou None."""
    return db.get(Income, income_id)


def create_income(db: Session, income: Income) -> Income:
    """Persiste uma nova receita."""
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

**Exports:** Todas as funcoes listadas.

**Decisoes:**
- Funcoes operam em instancias de modelo, nao em schemas Pydantic. A conversao e feita na camada de router/service.
- `create_expense` recebe um `Expense` ja construido. O chamador e responsavel por construi-lo a partir dos dados do schema.
- `update_expense` apenas chama `commit()` e `refresh()` porque o chamador muta a instancia antes de chamar update (padrao SQLAlchemy).

---

### 4.7 `backend/app/services.py`

**Responsabilidade:** Camada de logica de negocio. Contem o algoritmo de transicao de mes (RF-06) e auto-deteccao de status (RF-05). Este e o arquivo mais complexo do backend.

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


def generate_month_data(db: Session, target_mes: date) -> bool:
    """
    RF-06: Algoritmo de Transicao de Mes.

    Chamado quando o usuario navega para um mes sem dados.
    Olha os dados do mes anterior e gera entradas para target_mes
    seguindo as regras de replicacao.

    Retorna True se dados foram gerados, False se o mes-alvo ja tinha dados
    ou o mes anterior nao tinha dados (nada a replicar).

    Algoritmo:
    1. Checar se target_mes ja tem dados → se sim, return False (idempotente)
    2. Buscar despesas e receitas do mes anterior
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
    5. Todas as novas entradas recebem status = Pendente e novos UUIDs.
    """
    # Passo 1: Check de idempotencia
    existing_expenses = crud.count_expenses_by_month(db, target_mes)
    existing_incomes = len(crud.get_incomes_by_month(db, target_mes))
    if existing_expenses > 0 or existing_incomes > 0:
        return False

    # Passo 2: Buscar dados do mes anterior
    prev_mes = get_previous_month(target_mes)
    prev_expenses = crud.get_expenses_by_month(db, prev_mes)
    prev_incomes = crud.get_incomes_by_month(db, prev_mes)

    if not prev_expenses and not prev_incomes:
        return False

    # Passo 3: Replicar despesas
    for exp in prev_expenses:
        if exp.parcela_atual is not None and exp.parcela_total is not None:
            # Despesa parcelada
            if exp.parcela_atual < exp.parcela_total:
                new_exp = Expense(
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


def get_monthly_summary(db: Session, mes_referencia: date) -> dict:
    """
    Constroi a visao mensal completa.
    Passos:
    1. Tenta gerar dados do mes se vazio (RF-06)
    2. Busca despesas e receitas
    3. Aplica auto-deteccao de status (RF-05)
    4. Calcula totalizadores (RF-04)
    """
    # Passo 1: Auto-gerar se necessario
    generate_month_data(db, mes_referencia)

    # Passo 2: Buscar dados
    expenses = crud.get_expenses_by_month(db, mes_referencia)
    incomes = crud.get_incomes_by_month(db, mes_referencia)

    # Passo 3: Auto-detectar status de atraso
    today = date.today()
    apply_status_auto_detection(expenses, today)
    db.commit()  # Persiste mudancas de status

    # Passo 4: Calcular totalizadores
    total_despesas = sum(float(e.valor) for e in expenses)
    total_receitas = sum(float(i.valor) for i in incomes)

    return {
        "mes_referencia": mes_referencia,
        "total_despesas": round(total_despesas, 2),
        "total_receitas": round(total_receitas, 2),
        "saldo_livre": round(total_receitas - total_despesas, 2),
        "expenses": expenses,
        "incomes": incomes,
    }
```

**Exports:** `get_next_month`, `get_previous_month`, `adjust_vencimento_to_month`, `apply_status_auto_detection`, `generate_month_data`, `get_monthly_summary`

**Edge Cases do Algoritmo RF-06:**

1. **Vencimento dia > dias no mes-alvo:** Ex: despesa vence dia 31/jan, alvo e fevereiro. `adjust_vencimento_to_month` faz clamp para 28/fev (ou 29 em ano bissexto).

2. **Navegar 2+ meses para frente:** Se o usuario pula de janeiro direto para marco (sem ver fevereiro), o algoritmo so olha o mes anterior (fevereiro). Se fevereiro esta vazio, nada e gerado para marco. O usuario deve visitar meses em sequencia para a cadeia propagar. Isso e por design e consistente com o PRD ("com base no mes anterior").

3. **Usuario adiciona dados manualmente a mes futuro:** Se o usuario cria despesas para marco antes da geracao automatica, o check de idempotencia ve que marco ja tem dados e nao sobrescreve.

---

### 4.8 `backend/app/routers/__init__.py`

**Responsabilidade:** Arquivo vazio tornando `routers/` um pacote Python.

---

### 4.9 `backend/app/routers/months.py`

**Responsabilidade:** Endpoint principal da visao mensal.

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.schemas import MonthlySummary
from app import services

router = APIRouter(prefix="/api/months", tags=["months"])


@router.get("/{year}/{month}", response_model=MonthlySummary)
def get_monthly_view(year: int, month: int, db: Session = Depends(get_db)):
    """
    GET /api/months/2026/2 → visao mensal completa de fevereiro 2026.
    Dispara geracao de mes se vazio (RF-06).
    Aplica auto-deteccao de status (RF-05).
    Retorna despesas, receitas e totalizadores.
    """
    mes_referencia = date(year, month, 1)
    summary = services.get_monthly_summary(db, mes_referencia)
    return summary
```

**Exports:** `router`

**Decisoes:**
- URL `/api/months/{year}/{month}` e mais RESTful que query parameters e produz URLs limpas.
- Este unico endpoint alimenta toda a pagina de visao mensal. O frontend faz uma chamada e recebe tudo que precisa.

---

### 4.10 `backend/app/routers/expenses.py`

**Responsabilidade:** Endpoints CRUD para despesas (RF-01, RF-07).

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models import Expense, ExpenseStatus
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app import crud

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.post("/{year}/{month}", response_model=ExpenseResponse, status_code=201)
def create_expense(
    year: int, month: int, data: ExpenseCreate, db: Session = Depends(get_db)
):
    """Criar nova despesa no mes especificado."""
    mes_referencia = date(year, month, 1)
    expense = Expense(
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
    expense_id: str, data: ExpenseUpdate, db: Session = Depends(get_db)
):
    """Atualizar despesa existente. PATCH: apenas campos enviados sao alterados."""
    expense = crud.get_expense_by_id(db, expense_id)
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
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    """Excluir despesa por ID."""
    expense = crud.get_expense_by_id(db, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")
    crud.delete_expense(db, expense)


@router.post(
    "/{expense_id}/duplicate", response_model=ExpenseResponse, status_code=201
)
def duplicate_expense(expense_id: str, db: Session = Depends(get_db)):
    """RF-07: Duplicar despesa existente no mesmo mes."""
    original = crud.get_expense_by_id(db, expense_id)
    if not original:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")

    new_expense = Expense(
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

**Exports:** `router`

**Decisoes:**
- POST para criacao usa `/{year}/{month}` para especificar o mes-alvo. O `mes_referencia` e derivado do path, nao do body.
- PATCH (nao PUT) permite atualizacao parcial. `model_dump(exclude_unset=True)` garante que apenas campos explicitamente enviados sao atualizados.
- Toggle de status (Pendente ↔ Pago) e feito via PATCH com `{ "status": "Pago" }` ou `{ "status": "Pendente" }`. Nao precisa de endpoint especial.
- O endpoint de duplicar copia todos os campos mas reseta status para Pendente e gera novo UUID.

---

### 4.11 `backend/app/routers/incomes.py`

**Responsabilidade:** Endpoints CRUD para receitas (RF-02).

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.models import Income
from app.schemas import IncomeCreate, IncomeUpdate, IncomeResponse
from app import crud

router = APIRouter(prefix="/api/incomes", tags=["incomes"])


@router.post("/{year}/{month}", response_model=IncomeResponse, status_code=201)
def create_income(
    year: int, month: int, data: IncomeCreate, db: Session = Depends(get_db)
):
    """Criar nova receita no mes especificado."""
    mes_referencia = date(year, month, 1)
    income = Income(
        mes_referencia=mes_referencia,
        nome=data.nome,
        valor=data.valor,
        data=data.data,
        recorrente=data.recorrente,
    )
    return crud.create_income(db, income)


@router.patch("/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: str, data: IncomeUpdate, db: Session = Depends(get_db)
):
    """Atualizar receita existente."""
    income = crud.get_income_by_id(db, income_id)
    if not income:
        raise HTTPException(status_code=404, detail="Receita nao encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(income, field, value)

    return crud.update_income(db, income)


@router.delete("/{income_id}", status_code=204)
def delete_income(income_id: str, db: Session = Depends(get_db)):
    """Excluir receita por ID."""
    income = crud.get_income_by_id(db, income_id)
    if not income:
        raise HTTPException(status_code=404, detail="Receita nao encontrada")
    crud.delete_income(db, income)
```

**Exports:** `router`

---

### 4.12 `backend/app/main.py`

**Responsabilidade:** Entry point da aplicacao FastAPI. Configura lifespan, CORS e routers.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import expenses, incomes, months


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: nada a limpar para SQLite


app = FastAPI(
    title="Meu Controle API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(months.router)
app.include_router(expenses.router)
app.include_router(incomes.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
```

**Exports:** `app`

**Decisoes:**
- Usa `lifespan` async context manager conforme recomendado pelo FastAPI (o decorator `on_event` esta deprecado).
- `Base.metadata.create_all()` no startup. Tabelas sao criadas se nao existem; tabelas existentes nao sao alteradas.
- CORS permite `http://localhost:5173` (porta padrao do Vite dev server).
- Todas as rotas sob prefixo `/api/`.

**Comando para rodar:** `uvicorn app.main:app --reload` (a partir do diretorio `backend/`).

---

## 5. Frontend — Arquivos a Criar

### 5.1 `frontend/package.json`

**Responsabilidade:** Metadados do projeto e dependencias.

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
    "@tanstack/react-query": "^5.62.0"
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

**Notas:**
- Sem `axios` — usamos `fetch` nativo.
- Sem `react-router` — Fase 1 tem uma unica pagina. O mes e gerenciado como estado, nao como rota URL.

---

### 5.2 `frontend/vite.config.ts`

**Responsabilidade:** Configuracao de build do Vite.

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

**Decisoes:**
- Vite dev server faz proxy de `/api` para o FastAPI em `localhost:8000`. O frontend chama `/api/months/2026/2` sem se preocupar com CORS durante dev.
- Tailwind CSS v4 usa plugin Vite (`@tailwindcss/vite`) ao inves de PostCSS — nao precisa de `tailwind.config.js`.

---

### 5.3 `frontend/tsconfig.json`

**Responsabilidade:** Configuracao raiz TypeScript com project references.

```json
{
  "files": [],
  "references": [{ "path": "./tsconfig.app.json" }]
}
```

---

### 5.4 `frontend/tsconfig.app.json`

**Responsabilidade:** Opcoes do compilador TypeScript para codigo da aplicacao.

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

---

### 5.5 `frontend/index.html`

**Responsabilidade:** HTML entry point da SPA.

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

---

### 5.6 `frontend/src/index.css`

**Responsabilidade:** CSS global com import Tailwind v4 e customizacao de tema.

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
}
```

**Decisoes:**
- Tailwind CSS v4 usa `@import "tailwindcss"` ao inves das diretivas v3.
- Cores de status (`pendente`, `pago`, `atrasado`) definidas como tokens do tema para uso como `bg-pendente`, `text-pago`, etc.

---

### 5.7 `frontend/src/main.tsx`

**Responsabilidade:** Bootstrap da aplicacao React. Configura QueryClient.

```typescript
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
      <App />
    </QueryClientProvider>
  </StrictMode>
);
```

**Decisoes:**
- `staleTime: 5 minutos` — dados financeiros mensais nao mudam frequentemente.
- `retry: 1` — uma tentativa em caso de falha.

---

### 5.8 `frontend/src/types.ts`

**Responsabilidade:** Definicoes de tipos TypeScript espelhando os schemas Pydantic do backend.

```typescript
// ========== Expense Types ==========

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

// ========== Income Types ==========

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

// ========== Monthly Summary ==========

export interface MonthlySummary {
  mes_referencia: string;
  total_despesas: number;
  total_receitas: number;
  saldo_livre: number;
  expenses: Expense[];
  incomes: Income[];
}
```

---

### 5.9 `frontend/src/utils/format.ts`

**Responsabilidade:** Formatacao de moeda BRL e utilitarios de exibicao.

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

**Decisoes:**
- `Intl.NumberFormat` instanciado uma vez (o construtor e caro relativo a chamadas `format()`).
- `formatDateBR` mostra apenas DD/MM (sem ano) pois o ano e implicito pelo contexto da visao mensal.

---

### 5.10 `frontend/src/utils/date.ts`

**Responsabilidade:** Utilitarios de navegacao entre meses.

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

**Decisoes:**
- Meses em portugues sem acentos (consistente com o estilo do PRD).
- Mes e 1-indexed (1 = Janeiro) para combinar com o padrao da URL da API `/api/months/{year}/{month}`.

---

### 5.11 `frontend/src/services/api.ts`

**Responsabilidade:** Funcoes HTTP client encapsulando chamadas `fetch` para a API backend.

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
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

// ========== Monthly ==========

export function fetchMonthlySummary(
  year: number,
  month: number
): Promise<MonthlySummary> {
  return request<MonthlySummary>(`/months/${year}/${month}`);
}

// ========== Expenses ==========

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

export function duplicateExpense(id: string): Promise<Expense> {
  return request<Expense>(`/expenses/${id}/duplicate`, { method: "POST" });
}

// ========== Incomes ==========

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

**Decisoes:**
- O helper `request` centraliza tratamento de erros, parsing JSON e headers.
- `BASE_URL = "/api"` (relativo) funciona com o proxy do Vite em dev.

---

### 5.12 `frontend/src/hooks/useExpenses.ts`

**Responsabilidade:** Hooks TanStack Query para operacoes CRUD de despesas.

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

**Decisoes:**
- Cada mutation invalida a query key `["monthly-summary", year, month]` no sucesso. Isso dispara refetch da visao mensal completa, recalculando totais e re-aplicando auto-deteccao de status.
- Sem optimistic updates na Fase 1. A abordagem de refetch e mais simples e garante que a UI sempre reflete o estado do servidor.

---

### 5.13 `frontend/src/hooks/useIncomes.ts`

**Responsabilidade:** Hooks TanStack Query para operacoes CRUD de receitas. Mesmo padrao de `useExpenses.ts`.

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

---

### 5.14 `frontend/src/hooks/useMonthTransition.ts`

**Responsabilidade:** Hook central da aplicacao. Gerencia estado do mes atual e o fetch principal de dados.

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

**Decisoes:**
- Quando o usuario clica Anterior/Proximo, `setMonthRef` dispara re-render com nova `queryKey`, que dispara novo fetch. TanStack Query cacheia resultados anteriores, entao voltar a um mes ja visitado e instantaneo.
- Inicializa com o mes do calendario atual via `getCurrentMonthRef()`.

---

### 5.15 `frontend/src/components/MonthNavigator.tsx`

**Responsabilidade:** Barra de navegacao entre meses com botoes Anterior/Proximo e label do mes atual.

**Interface:**

```typescript
interface MonthNavigatorProps {
  year: number;
  month: number;
  onPrevious: () => void;
  onNext: () => void;
}
```

**Renderiza:**
- Flex row com 3 elementos: botao "< Anterior", label do mes (ex: "Fevereiro 2026"), botao "Proximo >".
- Usa `getMonthLabel(year, month)` de `utils/date.ts`.
- Estilo Tailwind: botoes com `px-4 py-2 text-primary font-semibold hover:text-primary-hover`, label centralizado com `text-xl font-bold`.

**Dependencias:** `utils/date.ts`

---

### 5.16 `frontend/src/components/StatusBadge.tsx`

**Responsabilidade:** Badge de status clicavel para despesas. Renderiza pill colorida. Clicar alterna entre Pendente e Pago.

**Interface:**

```typescript
interface StatusBadgeProps {
  status: ExpenseStatus;
  onClick: () => void;
}
```

**Renderiza:**
- Elemento `<button>` estilizado como pill badge.
- Mapeamento de cores:
  - `Pendente` → `bg-pendente/20 text-pendente` (amarelado)
  - `Pago` → `bg-pago/20 text-pago` (esverdeado)
  - `Atrasado` → `bg-atrasado/20 text-atrasado` (avermelhado)
- Exibe o texto do status.
- `cursor-pointer` para estados clicaveis.

**Logica de toggle:**
- Clicar em `Pendente` → muda para `Pago`
- Clicar em `Atrasado` → muda para `Pago` (usuario pagou despesa atrasada)
- Clicar em `Pago` → muda para `Pendente`

**Dependencias:** `types.ts`

---

### 5.17 `frontend/src/components/ExpenseFormModal.tsx`

**Responsabilidade:** Modal para criacao e edicao de despesas. Usado tanto para "Nova Despesa" quanto para "Editar Despesa".

**Interface:**

```typescript
interface ExpenseFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ExpenseCreate) => void;
  initialData?: Expense | null; // Se fornecido, estamos editando
}
```

**Campos do formulario:**
- `nome` (text input, obrigatorio)
- `valor` (number input, obrigatorio, step="0.01", min="0.01")
- `vencimento` (date input, obrigatorio)
- `parcela_atual` (number input, opcional)
- `parcela_total` (number input, opcional)
- `recorrente` (checkbox, default true)

**Comportamento:**
- Em modo edicao, campos pre-populados com `initialData`.
- Campos de parcela aparecem/desaparecem juntos. Se um e preenchido, o outro se torna obrigatorio.
- Validacao client-side: `parcela_atual <= parcela_total`, ambos positivos.
- O checkbox `recorrente` e desabilitado quando campos de parcela estao preenchidos (PRD: "recorrente e ignorado na logica de transicao" para despesas parceladas).
- Ao submeter, chama `onSubmit` com os dados e fecha o modal.

**Estilo:**
- Overlay escuro (`bg-black/50`) com modal centralizado.
- Form com labels, inputs estilizados com Tailwind, botoes "Cancelar" e "Salvar".

**Dependencias:** `types.ts`

---

### 5.18 `frontend/src/components/IncomeFormModal.tsx`

**Responsabilidade:** Modal para criacao e edicao de receitas.

**Interface:**

```typescript
interface IncomeFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: IncomeCreate) => void;
  initialData?: Income | null;
}
```

**Campos do formulario:**
- `nome` (text input, obrigatorio)
- `valor` (number input, obrigatorio, step="0.01", min="0.01")
- `data` (date input, opcional)
- `recorrente` (checkbox, default true)

**Dependencias:** `types.ts`

---

### 5.19 `frontend/src/components/ConfirmDialog.tsx`

**Responsabilidade:** Dialogo de confirmacao para acoes de exclusao.

**Interface:**

```typescript
interface ConfirmDialogProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}
```

**Renderiza:**
- Overlay modal com titulo, mensagem e dois botoes: "Cancelar" (secundario) e "Confirmar" (vermelho/danger).

---

### 5.20 `frontend/src/components/IncomeTable.tsx`

**Responsabilidade:** Renderiza a secao RECEITAS da visao mensal.

**Interface:**

```typescript
interface IncomeTableProps {
  incomes: Income[];
  totalReceitas: number;
  year: number;
  month: number;
}
```

**Renderiza:**
- Header da secao: "RECEITAS" com botao "+ Nova Receita".
- Tabela com colunas: Nome | Valor | Data | Acoes.
- Cada linha mostra dados da receita com botoes Editar e Excluir.
- Linha footer: "TOTAL RECEITAS" com `formatBRL(totalReceitas)`.
- Gerencia seu proprio estado de modal para criar/editar.
- Usa hooks `useCreateIncome`, `useUpdateIncome`, `useDeleteIncome`.

**Dependencias:** `types.ts`, `utils/format.ts`, `hooks/useIncomes.ts`, `IncomeFormModal.tsx`, `ConfirmDialog.tsx`

---

### 5.21 `frontend/src/components/ExpenseTable.tsx`

**Responsabilidade:** Renderiza a secao DESPESAS da visao mensal. Componente mais rico em features da UI.

**Interface:**

```typescript
interface ExpenseTableProps {
  expenses: Expense[];
  totalDespesas: number;
  year: number;
  month: number;
}
```

**Renderiza:**
- Header da secao: "DESPESAS" com botao "+ Nova Despesa".
- Tabela com colunas: Nome | Valor | Parcela | Venc. | Status | Acoes.
- Cada linha usa `StatusBadge` para o status clicavel.
- Coluna Parcela mostra `formatParcela(parcela_atual, parcela_total)` ou vazio.
- Coluna Venc. mostra `formatDateBR(vencimento)` (DD/MM).
- Coluna Valor mostra `formatBRL(valor)`.
- Botoes de acao: Editar, Duplicar, Excluir.
- Linha footer: "TOTAL DESPESAS" com `formatBRL(totalDespesas)`.
- Gerencia estado de modal para criar/editar e dialogo de confirmacao para excluir.

**Logica de status toggle:**
- Clicar `StatusBadge` chama `useUpdateExpense` com `{ status: novoStatus }`:
  - Pendente/Atrasado → `{ status: "Pago" }`
  - Pago → `{ status: "Pendente" }`

**Logica de duplicar:**
- Clicar botao Duplicar chama `useDuplicateExpense(expense.id)`.

**Dependencias:** `types.ts`, `utils/format.ts`, `hooks/useExpenses.ts`, `StatusBadge.tsx`, `ExpenseFormModal.tsx`, `ConfirmDialog.tsx`

---

### 5.22 `frontend/src/components/SaldoLivre.tsx`

**Responsabilidade:** Renderiza a barra de SALDO LIVRE.

**Interface:**

```typescript
interface SaldoLivreProps {
  totalReceitas: number;
  totalDespesas: number;
  saldoLivre: number;
}
```

**Renderiza:**
- Card/barra mostrando: `SALDO LIVRE: R$ {receitas} - R$ {despesas} = R$ {saldo}`.
- Background verde se saldo >= 0, vermelho se saldo < 0.
- Usa `formatBRL` para todos os valores.
- Estilo: `p-4 rounded-lg text-white font-bold text-lg`.

**Dependencias:** `utils/format.ts`

---

### 5.23 `frontend/src/pages/MonthlyView.tsx`

**Responsabilidade:** Pagina principal (e unica). Compoe todos os componentes.

```typescript
import { useMonthlyView } from "../hooks/useMonthTransition";
import MonthNavigator from "../components/MonthNavigator";
import IncomeTable from "../components/IncomeTable";
import ExpenseTable from "../components/ExpenseTable";
import SaldoLivre from "../components/SaldoLivre";

export default function MonthlyView() {
  const {
    year,
    month,
    data,
    isLoading,
    isError,
    error,
    goToPreviousMonth,
    goToNextMonth,
  } = useMonthlyView();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-20">
        <p className="text-gray-500 text-lg">Carregando...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex justify-center items-center py-20">
        <p className="text-danger text-lg">
          Erro ao carregar dados: {error?.message}
        </p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
      <MonthNavigator
        year={year}
        month={month}
        onPrevious={goToPreviousMonth}
        onNext={goToNextMonth}
      />
      <IncomeTable
        incomes={data.incomes}
        totalReceitas={data.total_receitas}
        year={year}
        month={month}
      />
      <ExpenseTable
        expenses={data.expenses}
        totalDespesas={data.total_despesas}
        year={year}
        month={month}
      />
      <SaldoLivre
        totalReceitas={data.total_receitas}
        totalDespesas={data.total_despesas}
        saldoLivre={data.saldo_livre}
      />
    </div>
  );
}
```

**Decisoes:**
- `max-w-4xl mx-auto` centraliza com largura maxima razoavel para desktop, totalmente responsivo em mobile.
- `year` e `month` sao passados para componentes-filhos porque os hooks de mutation precisam deles (para saber qual cache invalidar).
- Estados de loading e error tratados neste nivel, mantendo componentes-filhos focados em renderizar dados.

---

### 5.24 `frontend/src/App.tsx`

**Responsabilidade:** Shell da aplicacao com header.

```typescript
import MonthlyView from "./pages/MonthlyView";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-primary text-white py-4 px-6 shadow-md">
        <h1 className="text-xl font-bold tracking-wide">MEU CONTROLE</h1>
      </header>
      <main>
        <MonthlyView />
      </main>
    </div>
  );
}
```

**Decisoes:**
- Sem biblioteca de roteamento. Fase 1 tem exatamente uma pagina.
- O header esta aqui (nao em MonthlyView) porque e chrome da aplicacao, nao conteudo de pagina.

---

## 6. `.gitignore`

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

## 7. Fluxos de Dados Detalhados

### 7.1 Carregamento da Visao Mensal (Fluxo Principal)

```
Usuario navega para um mes
    |
    v
MonthlyView.tsx
    | useMonthlyView() hook
    v
TanStack Query: queryKey = ["monthly-summary", 2026, 2]
    | queryFn: fetchMonthlySummary(2026, 2)
    v
api.ts: GET /api/months/2026/2
    | (Vite proxy → localhost:8000)
    v
months.py router: get_monthly_view(year=2026, month=2)
    |
    v
services.py: get_monthly_summary(db, date(2026,2,1))
    |
    |-- Passo 1: generate_month_data(db, date(2026,2,1))
    |     |-- Checar se fev tem dados (idempotencia)
    |     |-- Se vazio: buscar dados de jan, replicar por RF-06
    |     |-- Commit novos registros
    |
    |-- Passo 2: crud.get_expenses_by_month(db, date(2026,2,1))
    |-- Passo 3: crud.get_incomes_by_month(db, date(2026,2,1))
    |-- Passo 4: apply_status_auto_detection(expenses, today)
    |-- Passo 5: Calcular totalizadores
    |
    v
Retorna MonthlySummary JSON
    |
    v
TanStack Query cacheia resultado
    |
    v
MonthlyView renderiza:
    |-- MonthNavigator (year, month, callbacks nav)
    |-- IncomeTable (incomes, total)
    |-- ExpenseTable (expenses, total)
    |-- SaldoLivre (totais)
```

### 7.2 Toggle de Status

```
Usuario clica StatusBadge em uma despesa
    |
    v
ExpenseTable.tsx: determina novo status
    | Pendente/Atrasado → Pago
    | Pago → Pendente
    v
useUpdateExpense mutation
    | mutationFn: api.updateExpense(id, { status: "Pago" })
    v
api.ts: PATCH /api/expenses/{id}
    | body: { "status": "Pago" }
    v
expenses.py router: update_expense(expense_id, data)
    |-- Buscar despesa do DB
    |-- Aplicar update parcial (apenas campo status)
    |-- Commit
    v
Retorna ExpenseResponse atualizado
    |
    v
onSuccess: invalidateQueries(["monthly-summary", year, month])
    | TanStack Query refetch visao mensal completa
    v
UI re-renderiza com status atualizado
```

### 7.3 Criar Despesa

```
Usuario clica "+ Nova Despesa"
    |
    v
ExpenseTable.tsx: abre ExpenseFormModal (isOpen=true)
    |
    v
Usuario preenche form, clica "Salvar"
    |
    v
ExpenseFormModal: valida, chama onSubmit(formData)
    |
    v
ExpenseTable.tsx: useCreateExpense mutation
    | mutationFn: api.createExpense(year, month, data)
    v
api.ts: POST /api/expenses/2026/2
    | body: { nome, valor, vencimento, ... }
    v
expenses.py router: create_expense(year=2026, month=2, data)
    |-- Construir modelo Expense (mes_referencia=2026-02-01, status=Pendente)
    |-- crud.create_expense(db, expense)
    |-- Commit
    v
Retorna ExpenseResponse (201)
    |
    v
onSuccess: invalidateQueries(["monthly-summary", 2026, 2])
    | TanStack Query refetch → totais recalculados server-side
    v
UI re-renderiza com nova despesa na tabela e totais atualizados
```

---

## 8. Ordem de Implementacao

### Fase A — Backend Core (fazer primeiro):
1. `backend/requirements.txt`
2. `backend/app/__init__.py`
3. `backend/app/database.py`
4. `backend/app/models.py`
5. `backend/app/schemas.py`
6. `backend/app/crud.py`
7. `backend/app/services.py`
8. `backend/app/routers/__init__.py`
9. `backend/app/routers/months.py`
10. `backend/app/routers/expenses.py`
11. `backend/app/routers/incomes.py`
12. `backend/app/main.py`

### Fase B — Frontend Scaffolding:
13. `frontend/package.json`
14. `frontend/tsconfig.json` + `frontend/tsconfig.app.json`
15. `frontend/vite.config.ts`
16. `frontend/index.html`
17. `frontend/src/index.css`
18. `frontend/src/main.tsx`

### Fase C — Frontend Aplicacao (tipos primeiro, depois bottom-up):
19. `frontend/src/types.ts`
20. `frontend/src/utils/format.ts`
21. `frontend/src/utils/date.ts`
22. `frontend/src/services/api.ts`
23. `frontend/src/hooks/useExpenses.ts`
24. `frontend/src/hooks/useIncomes.ts`
25. `frontend/src/hooks/useMonthTransition.ts`
26. `frontend/src/components/ConfirmDialog.tsx`
27. `frontend/src/components/StatusBadge.tsx`
28. `frontend/src/components/MonthNavigator.tsx`
29. `frontend/src/components/SaldoLivre.tsx`
30. `frontend/src/components/ExpenseFormModal.tsx`
31. `frontend/src/components/IncomeFormModal.tsx`
32. `frontend/src/components/IncomeTable.tsx`
33. `frontend/src/components/ExpenseTable.tsx`
34. `frontend/src/pages/MonthlyView.tsx`
35. `frontend/src/App.tsx`

### Fase D — Arquivo raiz:
36. `.gitignore`

---

## 9. Verificacao

### 9.1 Backend isolado:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
- GET http://localhost:8000/api/health → `{"status": "ok"}`
- GET http://localhost:8000/docs → Swagger UI com todos os endpoints documentados

### 9.2 Frontend isolado:
```bash
cd frontend
npm install
npm run dev
```
- Abrir http://localhost:5173 → pagina carrega sem erros no console

### 9.3 Fluxo completo (backend + frontend rodando):
- [ ] Criar receita via "+ Nova Receita" → aparece na tabela, total atualiza
- [ ] Criar despesa via "+ Nova Despesa" → aparece na tabela, total e saldo atualizam
- [ ] Clicar no status "Pendente" → muda para "Pago"
- [ ] Clicar no status "Pago" → volta para "Pendente"
- [ ] Editar despesa → valores atualizam na tabela e totalizadores
- [ ] Excluir despesa → some da tabela, totalizadores recalculam
- [ ] Duplicar despesa → nova entrada identica com status Pendente
- [ ] Navegar para proximo mes (sem dados) → dados gerados automaticamente do mes anterior
- [ ] Despesa recorrente do mes anterior → aparece no proximo mes
- [ ] Despesa parcelada "5 de 11" → proximo mes mostra "6 de 11"
- [ ] Despesa parcelada "11 de 11" → NAO aparece no proximo mes
- [ ] Despesa nao recorrente → NAO aparece no proximo mes
- [ ] Receita recorrente → aparece no proximo mes
- [ ] Receita nao recorrente → NAO aparece no proximo mes
- [ ] Despesa com vencimento passado e status Pendente → exibida como "Atrasado"
- [ ] Formato monetario: R$ 1.234,56 em todos os valores
- [ ] Interface responsiva em mobile (testar com DevTools)

---

*Documento gerado em 2026-02-06. SPEC v1.0 — Fase 1.*
