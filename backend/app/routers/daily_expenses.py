"""CR-005: Router para gastos diários."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.auth import get_current_user
from app.models import DailyExpense, User
from app.schemas import (
    DailyExpenseCreate,
    DailyExpenseUpdate,
    DailyExpenseResponse,
    DailyExpenseMonthlySummary,
    CategoriesResponse,
)
from app.categories import (
    DAILY_EXPENSE_CATEGORIES,
    PAYMENT_METHODS,
    get_category_for_subcategory,
    is_valid_payment_method,
)
from app import crud, services

router = APIRouter(prefix="/api/daily-expenses", tags=["daily-expenses"])


@router.get("/categories", response_model=CategoriesResponse)
def get_categories():
    """Retorna categorias, subcategorias e metodos de pagamento disponiveis."""
    return {
        "categorias": DAILY_EXPENSE_CATEGORIES,
        "metodos_pagamento": PAYMENT_METHODS,
    }


@router.get("/{year}/{month}", response_model=DailyExpenseMonthlySummary)
def get_daily_expenses_monthly(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Visao mensal de gastos diarios, agrupados por dia."""
    mes_referencia = date(year, month, 1)
    return services.get_daily_expenses_monthly_summary(db, mes_referencia, current_user.id)


@router.post("/{year}/{month}", response_model=DailyExpenseResponse, status_code=201)
def create_daily_expense(
    year: int,
    month: int,
    data: DailyExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Criar novo gasto diario no mes especificado."""
    # Validar subcategoria
    categoria = get_category_for_subcategory(data.subcategoria)
    if categoria is None:
        raise HTTPException(
            status_code=422,
            detail=f"Subcategoria inválida: {data.subcategoria}",
        )

    # Validar metodo de pagamento
    if not is_valid_payment_method(data.metodo_pagamento):
        raise HTTPException(
            status_code=422,
            detail=f"Método de pagamento inválido: {data.metodo_pagamento}",
        )

    mes_referencia = date(year, month, 1)
    daily_expense = DailyExpense(
        user_id=current_user.id,
        mes_referencia=mes_referencia,
        descricao=data.descricao,
        valor=data.valor,
        data=data.data,
        categoria=categoria,
        subcategoria=data.subcategoria,
        metodo_pagamento=data.metodo_pagamento,
    )
    return crud.create_daily_expense(db, daily_expense)


@router.patch("/{daily_expense_id}", response_model=DailyExpenseResponse)
def update_daily_expense(
    daily_expense_id: str,
    data: DailyExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualizar gasto diario existente."""
    daily_expense = crud.get_daily_expense_by_id(db, daily_expense_id, current_user.id)
    if not daily_expense:
        raise HTTPException(status_code=404, detail="Gasto diário não encontrado")

    update_data = data.model_dump(exclude_unset=True)

    # Se subcategoria mudou, re-derivar categoria
    if "subcategoria" in update_data:
        categoria = get_category_for_subcategory(update_data["subcategoria"])
        if categoria is None:
            raise HTTPException(
                status_code=422,
                detail=f"Subcategoria inválida: {update_data['subcategoria']}",
            )
        update_data["categoria"] = categoria

    # Validar metodo de pagamento se mudou
    if "metodo_pagamento" in update_data:
        if not is_valid_payment_method(update_data["metodo_pagamento"]):
            raise HTTPException(
                status_code=422,
                detail=f"Método de pagamento inválido: {update_data['metodo_pagamento']}",
            )

    for field, value in update_data.items():
        setattr(daily_expense, field, value)

    return crud.update_daily_expense(db, daily_expense)


@router.delete("/{daily_expense_id}", status_code=204)
def delete_daily_expense(
    daily_expense_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Excluir gasto diario por ID."""
    daily_expense = crud.get_daily_expense_by_id(db, daily_expense_id, current_user.id)
    if not daily_expense:
        raise HTTPException(status_code=404, detail="Gasto diário não encontrado")
    crud.delete_daily_expense(db, daily_expense)
