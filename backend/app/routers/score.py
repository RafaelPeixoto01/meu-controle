"""CR-026: Endpoints do Score de Saude Financeira."""
import json
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app import crud
from app.services import get_monthly_summary, get_previous_month, apply_status_auto_detection
from app.health_score import calculate_health_score, calculate_conservative_score, generate_actions
from app.schemas import HealthScoreResponse, ScoreHistoryResponse

router = APIRouter(prefix="/api/score", tags=["score"])


@router.get("", response_model=HealthScoreResponse)
def get_health_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calcula e retorna o score de saude financeira do mes atual."""
    today = date.today()
    mes_atual = date(today.year, today.month, 1)
    user_id = current_user.id

    # 1. Buscar dados do mes atual (com auto-generate e status detection)
    monthly = get_monthly_summary(db, mes_atual, user_id)
    expenses = monthly["expenses"]
    renda = monthly["total_receitas"]

    # 2. Gastos diarios do mes
    daily_expenses = crud.get_daily_expenses_by_month(db, mes_atual, user_id)

    # 3. Grupos de parcelas
    installments_data = crud.get_installment_expenses_grouped(db, user_id)
    installment_groups = installments_data["groups"]

    # 4. Historico de gastos diarios (3 meses anteriores para media de variaveis)
    daily_expense_history = []
    check_mes = get_previous_month(mes_atual)
    for _ in range(3):
        total = crud.get_daily_expense_total_by_month(db, check_mes, user_id)
        if total > 0:
            daily_expense_history.append((check_mes, total))
        check_mes = get_previous_month(check_mes)
    daily_expense_history.reverse()  # cronologico

    # 5. Comprometimento do mes anterior (para D4c tendencia)
    prev_mes = get_previous_month(mes_atual)
    prev_score = crud.get_score_by_month(db, user_id, prev_mes)
    if prev_score:
        prev_comprometimento = prev_score.d1_comprometimento  # Use stored D1 as proxy
        # Better: calculate actual comprometimento from stored data
        snapshot = json.loads(prev_score.dados_snapshot) if prev_score.dados_snapshot else {}
        prev_comprometimento = snapshot.get("comprometimento_pct")
    else:
        prev_comprometimento = None

    # 6. Calcular score
    score_data = calculate_health_score(
        renda=renda,
        expenses=expenses,
        daily_expenses=daily_expenses,
        installment_groups=installment_groups,
        daily_expense_history=daily_expense_history,
        prev_month_comprometimento=prev_comprometimento,
        mes_atual=mes_atual,
    )

    # 7. Cenario conservador
    cenario_conservador = calculate_conservative_score(score_data, installment_groups, renda)

    # 8. Gerar acoes sugeridas
    acoes = generate_actions(score_data, renda, expenses, daily_expenses, installment_groups)

    # 9. Variacao vs mes anterior
    variacao = None
    if prev_score:
        variacao = score_data["score"]["total"] - prev_score.score_total

    # 10. Persistir score do mes atual
    dims = score_data["dimensoes"]
    total_fixos = sum(float(e.valor) for e in expenses)
    total_variaveis = sum(float(de.valor) for de in daily_expenses)
    comprometimento_pct = round((total_fixos + total_variaveis) / renda * 100, 1) if renda > 0 else 0

    persist_data = {
        "score_total": score_data["score"]["total"],
        "d1_comprometimento": dims["d1_comprometimento"]["pontos"],
        "d2_parcelas": dims["d2_parcelas"]["pontos"],
        "d3_poupanca": dims["d3_poupanca"]["pontos"],
        "d4_comportamento": dims["d4_comportamento"]["pontos"],
        "classificacao": score_data["score"]["classificacao"],
        "score_conservador": cenario_conservador["score"] if cenario_conservador else None,
        "dados_snapshot": {
            "renda": renda,
            "total_fixos": total_fixos,
            "total_variaveis": total_variaveis,
            "comprometimento_pct": comprometimento_pct,
            "qtd_parcelas": len([g for g in installment_groups if g["status_geral"] == "Em andamento"]),
        },
    }
    crud.upsert_score_historico(db, user_id, mes_atual, persist_data)

    # 11. Montar resposta
    response = {
        "score": {
            **score_data["score"],
            "variacao_mes_anterior": variacao,
        },
        "dimensoes": score_data["dimensoes"],
        "cenario_conservador": cenario_conservador,
        "acoes": acoes,
    }

    return response


@router.get("/history", response_model=ScoreHistoryResponse)
def get_score_history(
    months: int = Query(12, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna historico de scores mensais para grafico de evolucao."""
    records = crud.get_score_history(db, current_user.id, months)

    historico = [
        {
            "mes_referencia": r.mes_referencia.strftime("%Y-%m"),
            "score_total": r.score_total,
            "classificacao": r.classificacao,
            "d1": r.d1_comprometimento,
            "d2": r.d2_parcelas,
            "d3": r.d3_poupanca,
            "d4": r.d4_comportamento,
        }
        for r in records
    ]

    return {
        "historico": historico,
        "meses_solicitados": months,
        "meses_disponiveis": len(historico),
    }
