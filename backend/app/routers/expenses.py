from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.auth import get_current_user  # CR-002
from app.models import Expense, ExpenseStatus, User  # CR-002: User
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse, InstallmentsResponse
from app import crud

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.get("/installments", response_model=InstallmentsResponse)
def get_installments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna todas as despesas parceladas agrupadas por compra.
    """
    return crud.get_installment_expenses_grouped(db, current_user.id)


# NOTE: duplicate route MUST be before create route to avoid
# /{year}/{month} matching /{expense_id}/duplicate
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


from app.utils import add_months

@router.post("/{year}/{month}", response_model=ExpenseResponse, status_code=201)
def create_expense(
    year: int,
    month: int,
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """
    Criar nova despesa no mes especificado. 
    Se for parcelada (parcela_total > 1), CRIA AUTOMATICAMENTE todas as parcelas futuras.
    """
    mes_referencia_inicial = date(year, month, 1)
    
    # Validações básicas
    if data.parcela_total > 1 and data.parcela_atual > data.parcela_total:
        raise HTTPException(status_code=400, detail="Parcela atual nao pode ser maior que total")

    # 1. Criar a despesa do mês atual (que será retornada)
    expense_atual = Expense(
        user_id=current_user.id,
        mes_referencia=mes_referencia_inicial,
        nome=data.nome,
        valor=data.valor,
        vencimento=data.vencimento,
        parcela_atual=data.parcela_atual,
        parcela_total=data.parcela_total,
        recorrente=data.recorrente,
        status=ExpenseStatus.PENDENTE.value,
    )
    db.add(expense_atual)
    
    # 2. Se for parcelada, criar as futuras (apenas se nao for recorrente infinita, que tem logica propria)
    # Assumindo que 'recorrente' flag é para fixas mensais (Netflix) e 'parcela_total > 1' é compras parceladas (Notebook)
    if data.parcela_total > 1:
        # Quantas parcelas faltam criar?
        # Se usuario ta criando parcela 1 de 10, faltam 9 (2 a 10)
        start_p = data.parcela_atual + 1
        end_p = data.parcela_total
        
        for i in range(start_p, end_p + 1):
            offset_months = i - data.parcela_atual
            
            # Calcular proximo mes de referencia
            next_mes = add_months(mes_referencia_inicial, offset_months)
            
            # Calcular proximo vencimento (mantendo dia se possivel)
            next_venc = add_months(data.vencimento, offset_months)
            
            future_expense = Expense(
                user_id=current_user.id,
                mes_referencia=next_mes,
                nome=data.nome,
                valor=data.valor,
                vencimento=next_venc,
                parcela_atual=i,
                parcela_total=data.parcela_total,
                recorrente=False, # Parcelas futuras nao sao "recorrentes" no sentido de flag
                status=ExpenseStatus.PENDENTE.value
            )
            db.add(future_expense)

    db.commit()
    db.refresh(expense_atual)
    return expense_atual


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
    delete_all: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # CR-002
):
    """Excluir despesa por ID. Suporta exclusao em serie (CR-009)."""
    expense = crud.get_expense_by_id(db, expense_id, current_user.id)  # CR-002: ownership check
    if not expense:
        raise HTTPException(status_code=404, detail="Despesa nao encontrada")
    
    if delete_all and ((expense.parcela_total is not None and expense.parcela_total > 1) or expense.recorrente):
        crud.delete_expense_related(db, expense)
    else:
        crud.delete_expense(db, expense)
