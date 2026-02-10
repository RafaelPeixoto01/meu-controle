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
