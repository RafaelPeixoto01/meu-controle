"""CR-033: Endpoints de Alertas Inteligentes."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app import crud
from app.alerts import AlertEngine
from app.schemas import (
    AlertasResponse,
    AlertaOutput,
    AlertaAcao,
    AlertasResumo,
    ConfiguracaoAlertasResponse,
    ConfiguracaoAlertasUpdate,
)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertasResponse)
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calcula e retorna todos os alertas ativos do mes atual."""
    today = date.today()
    mes_atual = date(today.year, today.month, 1)

    engine = AlertEngine()
    result = engine.calcular_alertas(db, current_user.id, mes_atual)

    # Converter para schema de resposta
    alertas_output = []
    for a in result["alertas"]:
        acao = None
        if a.get("acao"):
            acao = AlertaAcao(**a["acao"])
        alertas_output.append(AlertaOutput(
            id=a.get("id"),
            tipo=a["tipo"],
            severidade=a["severidade"],
            titulo=a["titulo"],
            descricao=a.get("descricao", ""),
            impacto_mensal=a.get("impacto_mensal"),
            impacto_anual=a.get("impacto_anual"),
            status=a["status"],
            acao=acao,
            contexto_aba=a["contexto_aba"],
            created_at=a.get("created_at"),
        ))

    return AlertasResponse(
        alertas=alertas_output,
        resumo=AlertasResumo(**result["resumo"]),
    )


@router.patch("/{alerta_id}/seen")
def mark_alert_seen(
    alerta_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marca alerta como visto."""
    alerta = crud.get_alerta_by_id(db, alerta_id, current_user.id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")

    crud.mark_alerta_visto(db, alerta)
    return {"status": alerta.status, "visto_em": alerta.visto_em.isoformat() if alerta.visto_em else None}


@router.patch("/{alerta_id}/dismiss")
def dismiss_alert(
    alerta_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Marca alerta como dispensado."""
    alerta = crud.get_alerta_by_id(db, alerta_id, current_user.id)
    if not alerta:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")

    crud.mark_alerta_dispensado(db, alerta)
    return {"status": alerta.status, "dispensado_em": alerta.dispensado_em.isoformat() if alerta.dispensado_em else None}


@router.get("/config", response_model=ConfiguracaoAlertasResponse)
def get_alerts_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retorna configuracoes de alertas do usuario."""
    config = crud.get_configuracao_alertas(db, current_user.id)
    return ConfiguracaoAlertasResponse(
        antecedencia_vencimento=config.antecedencia_vencimento,
        alerta_atrasadas=config.alerta_atrasadas,
        alerta_parcelas_encerrando=config.alerta_parcelas_encerrando,
        alerta_score=config.alerta_score,
        alerta_comprometimento=config.alerta_comprometimento,
        limiar_comprometimento=config.limiar_comprometimento,
        alerta_parcela_ativada=config.alerta_parcela_ativada,
        alerta_ia=config.alerta_ia,
    )


@router.put("/config", response_model=ConfiguracaoAlertasResponse)
def update_alerts_config(
    data: ConfiguracaoAlertasUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Atualiza configuracoes de alertas do usuario."""
    config = crud.update_configuracao_alertas(
        db, current_user.id, data.model_dump(exclude_unset=True)
    )
    return ConfiguracaoAlertasResponse(
        antecedencia_vencimento=config.antecedencia_vencimento,
        alerta_atrasadas=config.alerta_atrasadas,
        alerta_parcelas_encerrando=config.alerta_parcelas_encerrando,
        alerta_score=config.alerta_score,
        alerta_comprometimento=config.alerta_comprometimento,
        limiar_comprometimento=config.limiar_comprometimento,
        alerta_parcela_ativada=config.alerta_parcela_ativada,
        alerta_ia=config.alerta_ia,
    )
