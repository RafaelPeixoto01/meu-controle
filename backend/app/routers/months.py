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
