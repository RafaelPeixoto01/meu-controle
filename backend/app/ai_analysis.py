"""
CR-032: Servico de analise financeira por IA.

Coleta dados financeiros, monta prompt, chama API Claude, parseia resposta
e mescla recomendacoes da IA com acoes do score deterministico (F04).
"""
import json
import logging
import os
import re
import time
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app import crud
from app.models import DailyExpense, ExpenseStatus
from app.services import get_monthly_summary, get_previous_month
from app.health_score import calculate_health_score, calculate_conservative_score, generate_actions

import anthropic as anthropic_sdk

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


# ========== Data Collector ==========

def collect_analysis_data(db: Session, user_id: str, mes_referencia: date) -> dict:
    """
    Agrega dados financeiros do mes de referencia para montar o prompt da IA.
    Reutiliza o mesmo padrao de coleta do endpoint /api/score.
    """
    # 1. Dados do mes (com auto-generate e status detection)
    monthly = get_monthly_summary(db, mes_referencia, user_id)
    expenses = monthly["expenses"]
    renda = monthly["total_receitas"]

    # 2. Gastos diarios do mes
    daily_expenses = crud.get_daily_expenses_by_month(db, mes_referencia, user_id)

    # 3. Grupos de parcelas
    installments_data = crud.get_installment_expenses_grouped(db, user_id)
    installment_groups = installments_data["groups"]

    # 4. Historico de gastos diarios (3 meses anteriores)
    daily_expense_history = []
    check_mes = get_previous_month(mes_referencia)
    for _ in range(3):
        total = crud.get_daily_expense_total_by_month(db, check_mes, user_id)
        if total > 0:
            daily_expense_history.append((check_mes, total))
        check_mes = get_previous_month(check_mes)
    daily_expense_history.reverse()

    # 5. Comprometimento do mes anterior (para D4c)
    prev_mes = get_previous_month(mes_referencia)
    prev_score = crud.get_score_by_month(db, user_id, prev_mes)
    if prev_score and prev_score.dados_snapshot:
        snapshot = json.loads(prev_score.dados_snapshot)
        prev_comprometimento = snapshot.get("comprometimento_pct")
    else:
        prev_comprometimento = None

    # 6. Calcular score deterministico
    score_data = calculate_health_score(
        renda=renda,
        expenses=expenses,
        daily_expenses=daily_expenses,
        installment_groups=installment_groups,
        daily_expense_history=daily_expense_history,
        prev_month_comprometimento=prev_comprometimento,
        mes_atual=mes_referencia,
    )

    # 7. Cenario conservador
    cenario = calculate_conservative_score(score_data, installment_groups, renda)
    score_conservador = cenario["score"] if cenario else score_data["score"]["total"]

    # 8. Acoes do F04
    acoes_f04 = generate_actions(score_data, renda, expenses, daily_expenses, installment_groups)

    # 9. Totais
    total_fixos = sum(float(e.valor) for e in expenses)
    total_variaveis = sum(float(de.valor) for de in daily_expenses)
    total_parcelas = sum(
        float(g["installments"][0].valor)
        for g in installment_groups
        if g["status_geral"] == "Em andamento" and g.get("installments")
    )
    saldo_restante = renda - total_fixos - total_variaveis

    # 10. Breakdown por categoria (gastos planejados)
    cat_planejados: dict[str, float] = {}
    for e in expenses:
        cat = e.categoria or "Sem categoria"
        cat_planejados[cat] = cat_planejados.get(cat, 0) + float(e.valor)

    # 11. Breakdown por categoria (gastos diarios)
    cat_diarios: dict[str, float] = {}
    for de in daily_expenses:
        cat = de.categoria or "Sem categoria"
        cat_diarios[cat] = cat_diarios.get(cat, 0) + float(de.valor)

    # 12. Dias de registro
    dias_registro = len(set(de.data for de in daily_expenses))

    # 13. Gastos nao planejados ultimos 3 meses (para deteccao de recorrentes)
    gastos_nao_planejados_3m: list[dict] = []
    check_mes = get_previous_month(mes_referencia)
    for i in range(3):
        mes_de = mes_referencia if i == 0 else check_mes
        des = crud.get_daily_expenses_by_month(db, mes_de, user_id)
        for de in des:
            gastos_nao_planejados_3m.append({
                "mes": mes_de.strftime("%Y-%m"),
                "descricao": de.descricao,
                "valor": float(de.valor),
                "categoria": de.categoria,
            })
        if i > 0:
            check_mes = get_previous_month(check_mes)

    # 14. Parcelas ativas detalhadas
    parcelas_lista = []
    for g in installment_groups:
        if g["status_geral"] != "Em andamento" or not g.get("installments"):
            continue
        inst = g["installments"][0]
        num_paid = sum(1 for i in g["installments"] if i.status == ExpenseStatus.PAGO.value)
        parcelas_lista.append(
            f"{g['nome']}: R$ {float(inst.valor):.2f}/mês, {num_paid}/{g['parcela_total']} pagas"
        )

    # 15. Historico de scores
    score_history = crud.get_score_history(db, user_id, 6)
    historico_str = ", ".join(
        f"{r.mes_referencia.strftime('%Y-%m')}: {r.score_total} ({r.classificacao})"
        for r in score_history
    ) if score_history else "Primeiro mês"

    # 16. Gastos planejados lista
    lista_planejados = []
    for e in expenses:
        status_str = e.status
        parcela_str = f" ({e.parcela_atual}/{e.parcela_total})" if e.parcela_total else ""
        lista_planejados.append(
            f"{e.nome}{parcela_str}: R$ {float(e.valor):.2f} — {status_str}"
        )

    # 17. Comparativo ultimos meses
    comparativo = []
    check_mes = get_previous_month(mes_referencia)
    for _ in range(3):
        total_exp = crud.get_expense_total_by_month(db, check_mes, user_id)
        total_inc = crud.get_income_total_by_month(db, check_mes, user_id)
        total_daily = crud.get_daily_expense_total_by_month(db, check_mes, user_id)
        if total_inc > 0 or total_exp > 0:
            comparativo.append(
                f"{check_mes.strftime('%Y-%m')}: Renda R$ {total_inc:.2f}, "
                f"Fixos R$ {total_exp:.2f}, Variáveis R$ {total_daily:.2f}"
            )
        check_mes = get_previous_month(check_mes)
    comparativo.reverse()

    dims = score_data["dimensoes"]

    return {
        "score_data": score_data,
        "acoes_f04": acoes_f04,
        "prompt_data": {
            "score_total": score_data["score"]["total"],
            "classificacao": score_data["score"]["classificacao"],
            "d1": dims["d1_comprometimento"]["pontos"],
            "d1_detalhe": dims["d1_comprometimento"]["detalhe"],
            "d2": dims["d2_parcelas"]["pontos"],
            "d2_detalhe": dims["d2_parcelas"]["detalhe"],
            "d3": dims["d3_poupanca"]["pontos"],
            "d3_detalhe": dims["d3_poupanca"]["detalhe"],
            "d4": dims["d4_comportamento"]["pontos"],
            "d4_detalhe": dims["d4_comportamento"]["detalhe"],
            "score_conservador": score_conservador,
            "historico_scores": historico_str,
            "mes_referencia": mes_referencia.strftime("%B/%Y"),
            "renda_liquida": f"{renda:.2f}",
            "total_planejados": f"{total_fixos:.2f}",
            "total_nao_planejados": f"{total_variaveis:.2f}",
            "total_parcelas": f"{total_parcelas:.2f}",
            "saldo_restante": f"{saldo_restante:.2f}",
            "dias_registro": dias_registro,
            "breakdown_categorias": _format_category_breakdown(cat_planejados, cat_diarios, renda),
            "lista_gastos_planejados": "\n  ".join(lista_planejados) if lista_planejados else "Nenhum gasto planejado",
            "lista_gastos_nao_planejados": _format_daily_expenses_3m(gastos_nao_planejados_3m),
            "lista_parcelas": "\n  ".join(parcelas_lista) if parcelas_lista else "Nenhuma parcela ativa",
            "projecao_3_meses": "Dados de projeção não disponíveis",
            "comparativo_ultimos_meses": "\n  ".join(comparativo) if comparativo else "Primeiro mês de uso",
        },
    }


def _format_category_breakdown(cat_planejados: dict, cat_diarios: dict, renda: float) -> str:
    """Formata breakdown de categorias para o prompt."""
    lines = []
    all_cats: dict[str, float] = {}
    for cat, val in cat_planejados.items():
        all_cats[cat] = all_cats.get(cat, 0) + val
    for cat, val in cat_diarios.items():
        all_cats[cat] = all_cats.get(cat, 0) + val

    sorted_cats = sorted(all_cats.items(), key=lambda x: x[1], reverse=True)[:10]
    for cat, total in sorted_cats:
        pct = (total / renda * 100) if renda > 0 else 0
        planej = cat_planejados.get(cat, 0)
        diario = cat_diarios.get(cat, 0)
        parts = []
        if planej > 0:
            parts.append(f"fixo R$ {planej:.2f}")
        if diario > 0:
            parts.append(f"variável R$ {diario:.2f}")
        lines.append(f"{cat}: R$ {total:.2f} ({pct:.1f}% da renda) — {', '.join(parts)}")

    return "\n  ".join(lines) if lines else "Sem dados de categorias"


def _format_daily_expenses_3m(gastos: list[dict]) -> str:
    """Formata gastos nao planejados dos ultimos 3 meses."""
    if not gastos:
        return "Sem gastos não planejados registrados"

    # Agrupar por descricao para detectar recorrencia
    by_desc: dict[str, list] = {}
    for g in gastos:
        key = g["descricao"].lower().strip()
        by_desc.setdefault(key, []).append(g)

    lines = []
    # Top 30 por valor
    sorted_gastos = sorted(gastos, key=lambda x: x["valor"], reverse=True)[:30]
    for g in sorted_gastos:
        lines.append(f"{g['mes']} — {g['descricao']}: R$ {g['valor']:.2f} ({g['categoria']})")

    return "\n  ".join(lines)


# ========== Minimum Data Check ==========

def has_minimum_data(db: Session, user_id: str, mes_referencia: date) -> bool:
    """Verifica se ha dados suficientes para gerar analise."""
    daily_expenses = crud.get_daily_expenses_by_month(db, mes_referencia, user_id)
    dias_registro = len(set(de.data for de in daily_expenses))

    expenses = crud.get_expenses_by_month(db, mes_referencia, user_id)

    return dias_registro >= 7 or len(expenses) >= 5


# ========== Prompt Builder ==========

def build_prompts(data: dict) -> tuple[str, str]:
    """Carrega e interpola os prompts com os dados financeiros."""
    system_path = PROMPTS_DIR / "financial_analysis_system.txt"
    user_path = PROMPTS_DIR / "financial_analysis_user.txt"

    system_prompt = system_path.read_text(encoding="utf-8")
    user_template = user_path.read_text(encoding="utf-8")

    # Substituir placeholders {{key}} com valores do dict
    prompt_data = data["prompt_data"]
    user_prompt = user_template
    for key, value in prompt_data.items():
        user_prompt = user_prompt.replace(f"{{{{{key}}}}}", str(value))

    return system_prompt, user_prompt


# ========== Anthropic Client ==========

def call_anthropic_api(system_prompt: str, user_prompt: str) -> dict:
    """
    Chama a API Claude para gerar analise financeira.
    Retorna dict com resultado parseado e metadata.
    Raises Exception em caso de erro.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY não configurada")

    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
    timeout_seconds = int(os.getenv("AI_ANALYSIS_TIMEOUT_SECONDS", "30"))

    client = anthropic_sdk.Anthropic(api_key=api_key, timeout=timeout_seconds)

    start_time = time.time()
    max_retries = 2
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Extrair texto da resposta
            raw_text = response.content[0].text.strip()

            # Tentar parsear JSON
            resultado = _parse_ai_json(raw_text)

            return {
                "resultado": resultado,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "modelo": model,
                "tempo_processamento_ms": elapsed_ms,
                "raw_response": raw_text,
            }

        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))
                continue
            raise ValueError(f"IA retornou JSON inválido após {max_retries + 1} tentativas") from e

        except Exception as e:
            last_error = e
            logger.warning(f"Anthropic API error on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))
                continue
            raise

    raise last_error  # Should not reach here, but safety net


def _parse_ai_json(raw_text: str) -> dict:
    """Parseia JSON da resposta da IA, com tentativa de reparo."""
    # Remover possivel markdown wrapper
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Tentar reparar JSON truncado (fechar chaves/colchetes)
        repaired = text
        open_braces = repaired.count("{") - repaired.count("}")
        open_brackets = repaired.count("[") - repaired.count("]")
        repaired += "]" * max(0, open_brackets)
        repaired += "}" * max(0, open_braces)

        return json.loads(repaired)  # Raises JSONDecodeError if still invalid


# ========== Action Merger ==========

def merge_actions(acoes_f04: list[dict], recomendacoes_ia: list[dict]) -> list[dict]:
    """
    Mescla acoes do score deterministico (F04) com recomendacoes da IA.
    IA prevalece quando ambas cobrem a mesma dimensao.
    """
    resultado = []

    # Primeiro, todas as recomendacoes da IA
    for rec in recomendacoes_ia:
        resultado.append({
            "fonte": "ia",
            "acao": rec.get("acao", ""),
            "justificativa": rec.get("justificativa", ""),
            "impacto_score": rec.get("impacto_score_estimado", 0),
            "economia_mensal": rec.get("economia_estimada_mensal", 0),
            "dificuldade": rec.get("dificuldade", ""),
        })

    # Depois, acoes da F04 que nao tem equivalente na IA
    # Equivalencia: mesma dimensao_alvo
    dimensoes_cobertas_ia = set()
    # Tentar mapear recomendacoes da IA para dimensoes (heuristica simples)
    for rec in recomendacoes_ia:
        acao_lower = rec.get("acao", "").lower()
        if any(kw in acao_lower for kw in ["fix", "despesa", "gasto fixo", "comprometimento"]):
            dimensoes_cobertas_ia.add("d1_comprometimento")
        if any(kw in acao_lower for kw in ["parcela", "parcelamento"]):
            dimensoes_cobertas_ia.add("d2_parcelas")
        if any(kw in acao_lower for kw in ["poupança", "poupar", "economizar", "saldo"]):
            dimensoes_cobertas_ia.add("d3_poupanca")
        if any(kw in acao_lower for kw in ["registr", "pontualidade", "atraso", "pagamento"]):
            dimensoes_cobertas_ia.add("d4_comportamento")

    for acao in acoes_f04:
        if acao.get("dimensao_alvo") not in dimensoes_cobertas_ia:
            resultado.append({
                "fonte": "score",
                "acao": acao.get("descricao", ""),
                "justificativa": None,
                "impacto_score": acao.get("impacto_estimado", 0),
                "economia_mensal": None,
                "dificuldade": None,
            })

    # Ordenar por impacto e limitar
    resultado.sort(key=lambda x: x.get("impacto_score", 0), reverse=True)
    return resultado[:5]
