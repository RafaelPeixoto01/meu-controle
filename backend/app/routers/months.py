from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.auth import get_current_user  # CR-002
from app.models import User  # CR-002
from app.schemas import MonthlySummary
from app import services, crud

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


@router.get("/{year}/{month}/debug")
def debug_monthly_view(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """TEMPORARY: Inspeciona dados do mes sem disparar geracao automatica."""
    mes = date(year, month, 1)
    prev_mes = services.get_previous_month(mes)

    expenses = crud.get_expenses_by_month(db, mes, current_user.id)
    incomes = crud.get_incomes_by_month(db, mes, current_user.id)
    prev_expenses = crud.get_expenses_by_month(db, prev_mes, current_user.id)
    prev_incomes = crud.get_incomes_by_month(db, prev_mes, current_user.id)

    return {
        "user_id": current_user.id,
        "target_month": str(mes),
        "previous_month": str(prev_mes),
        "target_expenses_count": len(expenses),
        "target_incomes_count": len(incomes),
        "prev_expenses": [
            {
                "id": e.id,
                "nome": e.nome,
                "mes_referencia": str(e.mes_referencia),
                "recorrente": e.recorrente,
                "parcela_atual": e.parcela_atual,
                "parcela_total": e.parcela_total,
            }
            for e in prev_expenses
        ],
        "prev_incomes": [
            {
                "id": i.id,
                "nome": i.nome,
                "mes_referencia": str(i.mes_referencia),
                "recorrente": i.recorrente,
            }
            for i in prev_incomes
        ],
    }
