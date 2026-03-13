from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.schemas import DashboardResponse
from app import services

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{year}/{month}", response_model=DashboardResponse)
def get_dashboard(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CR-019: GET /api/dashboard/2026/3 → dados completos do dashboard.
    Retorna KPIs, breakdown por categoria (planejadas e diarios separados),
    evolucao 6 meses e status breakdown.
    """
    mes_referencia = date(year, month, 1)
    return services.get_dashboard_data(db, mes_referencia, current_user.id)
