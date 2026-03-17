"""CR-032: Endpoint de analise financeira por IA."""
import json
import logging
import os
from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, AnaliseFinanceira
from app import crud
from app.services import get_previous_month
from app.ai_analysis import (
    collect_analysis_data,
    has_minimum_data,
    build_prompts,
    call_anthropic_api,
    merge_actions,
)
from app.schemas import AiAnalysisResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["ai-analysis"])


@router.get("", response_model=AiAnalysisResponse)
def get_ai_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna analise financeira por IA do mes anterior.
    Gera automaticamente na primeira chamada do mes; retorna cache nas seguintes.
    """
    # 1. Feature flag
    if os.getenv("AI_ANALYSIS_ENABLED", "true").lower() != "true":
        return AiAnalysisResponse(
            status="indisponivel",
            reason="Análise por IA está desabilitada",
        )

    # 2. Determinar mes de referencia (mes anterior)
    today = date.today()
    mes_referencia = get_previous_month(date(today.year, today.month, 1))
    user_id = current_user.id

    # 3. Verificar cache
    cached = crud.get_analise_by_month(db, user_id, mes_referencia)
    if cached:
        resultado = json.loads(cached.resultado)
        return AiAnalysisResponse(
            status="disponivel",
            mes_referencia=mes_referencia.strftime("%Y-%m"),
            score_referencia=cached.score_referencia,
            resultado=resultado,
            modelo=cached.modelo,
            generated_at=cached.created_at.isoformat() if cached.created_at else None,
            is_cached=True,
        )

    # 4. Verificar dados minimos
    if not has_minimum_data(db, user_id, mes_referencia):
        return AiAnalysisResponse(
            status="indisponivel",
            mes_referencia=mes_referencia.strftime("%Y-%m"),
            reason="Dados insuficientes para análise do mês anterior. "
                   "São necessários pelo menos 7 dias de registro de gastos diários "
                   "ou 5 despesas planejadas.",
        )

    # 5. Verificar se API key esta configurada
    if not os.getenv("ANTHROPIC_API_KEY"):
        return AiAnalysisResponse(
            status="indisponivel",
            mes_referencia=mes_referencia.strftime("%Y-%m"),
            reason="Análise por IA não configurada. Configure ANTHROPIC_API_KEY.",
        )

    # 6. Coletar dados e gerar analise
    try:
        data = collect_analysis_data(db, user_id, mes_referencia)
        system_prompt, user_prompt = build_prompts(data)
        api_result = call_anthropic_api(system_prompt, user_prompt)

        resultado = api_result["resultado"]
        score_ref = data["score_data"]["score"]["total"]

        # 7. Persistir
        analise = AnaliseFinanceira(
            user_id=user_id,
            mes_referencia=mes_referencia,
            tipo="mensal",
            score_referencia=score_ref,
            dados_input=json.dumps(data["prompt_data"], ensure_ascii=False),
            resultado=json.dumps(resultado, ensure_ascii=False),
            tokens_input=api_result.get("tokens_input"),
            tokens_output=api_result.get("tokens_output"),
            modelo=api_result["modelo"],
            tempo_processamento_ms=api_result.get("tempo_processamento_ms"),
        )
        crud.create_analise(db, analise)

        return AiAnalysisResponse(
            status="disponivel",
            mes_referencia=mes_referencia.strftime("%Y-%m"),
            score_referencia=score_ref,
            resultado=resultado,
            modelo=api_result["modelo"],
            generated_at=datetime.now().isoformat(),
            is_cached=False,
        )

    except Exception as e:
        logger.error(f"Erro ao gerar análise IA: {e}", exc_info=True)
        return AiAnalysisResponse(
            status="erro",
            mes_referencia=mes_referencia.strftime("%Y-%m"),
            reason=f"Não foi possível gerar a análise: {type(e).__name__}",
        )
