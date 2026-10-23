"""CR-058: API de integracao para o Lumi (RF-22, RN-054, ADR-023).

So aceita o token de integracao (`get_integration_user`); o JWT do login e recusado.
Seis operacoes: categorias, lancar gasto diario, resumo de gastos por periodo, resumo
do mes, despesas planejadas do mes e status de uma despesa (Pago/Pendente).
Limite de 60 chamadas por minuto por token.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import crud, services
from app.auth import get_integration_user
from app.categories import (
    EXPENSE_CATEGORIES,
    PAYMENT_METHODS,
    get_category_for_subcategory,
    is_valid_payment_method,
)
from app.database import get_db
from app.models import DailyExpense, User
from app.rate_limit import integration_token_key, limiter
from app.schemas import (
    CategoriesResponse,
    DailyExpenseCreate,
    DailyExpenseResponse,
    IntegrationExpense,
    IntegrationExpenseStatusUpdate,
    IntegrationMonth,
    IntegrationPeriodSummary,
)
from app.utils import add_months

router = APIRouter(prefix="/api/integration/v1", tags=["integration"])

RATE_LIMIT = "60/minute"
MAX_PERIOD_DAYS = 93
MIN_YEAR = 2000


def _month(year: int, month: int) -> date:
    """Mes valido para a integracao: ate o mes seguinte ao atual. Abrir um mes gera os dados
    dele (RF-06), e o limite evita gerar meses distantes."""
    if not 1 <= month <= 12 or year < MIN_YEAR:
        raise HTTPException(status_code=422, detail="Mês inválido")
    mes_referencia = date(year, month, 1)
    if mes_referencia > add_months(date.today().replace(day=1), 1):
        raise HTTPException(status_code=422, detail="Mês além do próximo")
    return mes_referencia


@router.get("/categories", response_model=CategoriesResponse)
@limiter.limit(RATE_LIMIT, key_func=integration_token_key)
def integration_categories(request: Request, user: User = Depends(get_integration_user)):
    """Categorias, subcategorias e formas de pagamento (as mesmas do app)."""
    return {"categorias": EXPENSE_CATEGORIES, "metodos_pagamento": PAYMENT_METHODS}


@router.post("/daily-expenses", response_model=DailyExpenseResponse, status_code=201)
@limiter.limit(RATE_LIMIT, key_func=integration_token_key)
def integration_create_daily_expense(
    request: Request,
    data: DailyExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Lanca um gasto diario no mes da data do gasto, com as validacoes do app."""
    categoria = get_category_for_subcategory(data.subcategoria)
    if categoria is None:
        raise HTTPException(status_code=422, detail=f"Subcategoria inválida: {data.subcategoria}")
    if not is_valid_payment_method(data.metodo_pagamento):
        raise HTTPException(
            status_code=422, detail=f"Método de pagamento inválido: {data.metodo_pagamento}"
        )
    daily_expense = DailyExpense(
        user_id=user.id,
        mes_referencia=data.data.replace(day=1),
        descricao=data.descricao,
        valor=data.valor,
        data=data.data,
        categoria=categoria,
        subcategoria=data.subcategoria,
        metodo_pagamento=data.metodo_pagamento,
    )
    return crud.create_daily_expense(db, daily_expense)


@router.get("/daily-expenses/summary", response_model=IntegrationPeriodSummary)
@limiter.limit(RATE_LIMIT, key_func=integration_token_key)
def integration_daily_expenses_summary(
    request: Request,
    de: date,
    ate: date,
    categoria: str | None = None,
    subcategoria: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Total e totais por categoria e subcategoria dos gastos entre `de` e `ate`."""
    if de > ate:
        raise HTTPException(status_code=422, detail="Período inválido: de depois de ate")
    if (ate - de).days + 1 > MAX_PERIOD_DAYS:
        raise HTTPException(status_code=422, detail=f"Período maior que {MAX_PERIOD_DAYS} dias")
    return services.get_daily_expenses_period_summary(db, user.id, de, ate, categoria, subcategoria)


@router.get("/months/{year}/{month}", response_model=IntegrationMonth)
@limiter.limit(RATE_LIMIT, key_func=integration_token_key)
def integration_month(
    request: Request,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Resumo do mes: receitas, planejadas, gastos diarios, os dois saldos e os status."""
    return services.get_integration_month(db, _month(year, month), user.id)


@router.get("/expenses/{year}/{month}", response_model=list[IntegrationExpense])
@limiter.limit(RATE_LIMIT, key_func=integration_token_key)
def integration_expenses(
    request: Request,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Despesas planejadas do mes, por vencimento, com o status atualizado (RF-05)."""
    return services.get_monthly_summary(db, _month(year, month), user.id)["expenses"]


@router.patch("/expenses/{expense_id}", response_model=IntegrationExpense)
@limiter.limit(RATE_LIMIT, key_func=integration_token_key)
def integration_update_expense_status(
    request: Request,
    expense_id: str,
    data: IntegrationExpenseStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Muda so o status de uma despesa planejada do usuario, para Pago ou Pendente."""
    expense = crud.get_expense_by_id(db, expense_id, user.id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    expense.status = data.status.value
    return crud.update_expense(db, expense)
