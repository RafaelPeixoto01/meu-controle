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
