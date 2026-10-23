"""CR-058: API de integracao para o Lumi (RF-22, RN-054, ADR-023).

So aceita o token de integracao (`get_integration_user`); o JWT do login e recusado.
Seis operacoes: categorias, lancar gasto diario, resumo de gastos por periodo, resumo
do mes, despesas planejadas do mes e status de uma despesa (Pago/Pendente).
O limite de chamadas (60/min por token, 120/min por IP) vale para o router inteiro e
roda antes da autenticacao (`integration_rate_limit`).
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, services
from app.auth import get_integration_user
from app.categories import EXPENSE_CATEGORIES, PAYMENT_METHODS, get_category_for_subcategory
from app.database import get_db
from app.models import User
from app.rate_limit import integration_rate_limit
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

router = APIRouter(
    prefix="/api/integration/v1",
    tags=["integration"],
    dependencies=[Depends(integration_rate_limit)],
)

MAX_PERIOD_DAYS = 93
MIN_YEAR = 2000
# Lancamento por voz: um valor ou uma data mal ouvidos nao devem virar gasto (o Lumi tambem limita)
MAX_VALOR = 50_000.0
MAX_DAYS_AGO = 366
MAX_DAYS_AHEAD = 1  # folga de fuso entre o Lumi e o servidor


def _month(year: int, month: int) -> date:
    """Mes valido para a integracao: de 2000 ate o mes seguinte ao atual. Abrir um mes gera os
    dados dele (RF-06), e o limite evita gerar meses distantes."""
    if not 1 <= month <= 12 or not MIN_YEAR <= year <= date.today().year + 1:
        raise HTTPException(status_code=422, detail="Mês inválido")
    mes_referencia = date(year, month, 1)
    if mes_referencia > add_months(date.today().replace(day=1), 1):
        raise HTTPException(status_code=422, detail="Mês além do próximo")
    return mes_referencia


@router.get("/categories", response_model=CategoriesResponse)
def integration_categories(user: User = Depends(get_integration_user)):
    """Categorias, subcategorias e formas de pagamento (as mesmas do app)."""
    return {"categorias": EXPENSE_CATEGORIES, "metodos_pagamento": PAYMENT_METHODS}


@router.post("/daily-expenses", response_model=DailyExpenseResponse, status_code=201)
def integration_create_daily_expense(
    data: DailyExpenseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Lanca um gasto diario com as validacoes do app. Aqui o `mes_referencia` vem da data do
    gasto (como na importacao, RF-21): o Lumi nao escolhe mes."""
    if data.valor > MAX_VALOR:
        raise HTTPException(status_code=422, detail=f"Valor acima de {MAX_VALOR:,.0f}")
    today = date.today()
    if not today - timedelta(days=MAX_DAYS_AGO) <= data.data <= today + timedelta(days=MAX_DAYS_AHEAD):
        raise HTTPException(status_code=422, detail="Data fora do período aceito")
    try:
        daily_expense = services.new_daily_expense(user.id, data, data.data.replace(day=1))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return crud.create_daily_expense(db, daily_expense)


@router.get("/daily-expenses/summary", response_model=IntegrationPeriodSummary)
def integration_daily_expenses_summary(
    de: date,
    ate: date,
    categoria: str | None = None,
    subcategoria: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Total e totais por categoria e subcategoria dos gastos entre `de` e `ate`. Filtro vazio e
    ignorado; filtro que nao existe e recusado (um total zero enganaria o Lumi)."""
    if de > ate:
        raise HTTPException(status_code=422, detail="Período inválido: de depois de ate")
    if (ate - de).days + 1 > MAX_PERIOD_DAYS:
        raise HTTPException(status_code=422, detail=f"Período maior que {MAX_PERIOD_DAYS} dias")
    categoria = categoria or None
    subcategoria = subcategoria or None
    if categoria is not None and categoria not in EXPENSE_CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Categoria inválida: {categoria}")
    if subcategoria is not None and get_category_for_subcategory(subcategoria) is None:
        raise HTTPException(status_code=422, detail=f"Subcategoria inválida: {subcategoria}")
    return services.get_daily_expenses_period_summary(db, user.id, de, ate, categoria, subcategoria)


@router.get("/months/{year}/{month}", response_model=IntegrationMonth)
def integration_month(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Resumo do mes: receitas, planejadas, gastos diarios, os dois saldos e os status."""
    return services.get_integration_month(db, _month(year, month), user.id)


@router.get("/expenses/{year}/{month}", response_model=list[IntegrationExpense])
def integration_expenses(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Despesas planejadas do mes, por vencimento, com o status atualizado (RF-05)."""
    return services.get_monthly_summary(db, _month(year, month), user.id)["expenses"]


@router.patch("/expenses/{expense_id}", response_model=IntegrationExpense)
def integration_update_expense_status(
    expense_id: str,
    data: IntegrationExpenseStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_integration_user),
):
    """Muda so o status de uma despesa planejada do usuario, para Pago ou Pendente. Pendente com
    vencimento passado volta como Atrasado (RF-05), que e o que o app vai mostrar."""
    expense = crud.get_expense_by_id(db, expense_id, user.id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Despesa não encontrada")
    expense.status = data.status.value
    services.apply_status_auto_detection([expense], date.today())
    return crud.update_expense(db, expense)
