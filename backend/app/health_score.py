"""
CR-026: Servico de calculo do Score de Saude Financeira.

Calculo deterministico (sem IA), 0-100 pontos, 4 dimensoes ponderadas de 25 pontos cada:
- D1: Comprometimento com despesas fixas
- D2: Pressao de parcelas
- D3: Capacidade de poupanca
- D4: Comportamento e disciplina
"""
import calendar
from datetime import date

from app.models import Expense, DailyExpense, ExpenseStatus
from app.services import get_next_month


# ========== Classification ==========

SCORE_CLASSIFICATIONS = [
    (25, "Crítica", "#C0392B", "Situação exige ação imediata"),
    (45, "Atenção", "#E67E22", "Alguns pontos precisam de ajuste"),
    (65, "Estável", "#F1C40F", "Caminho certo, mas há espaço para melhorar"),
    (85, "Saudável", "#27AE60", "Finanças bem organizadas"),
    (100, "Excelente", "#1E8449", "Saúde financeira excepcional"),
]


def classify_score(total: int) -> tuple[str, str, str]:
    """Retorna (classificacao, cor_hex, mensagem) para um score total."""
    for limit, classificacao, cor, mensagem in SCORE_CLASSIFICATIONS:
        if total <= limit:
            return classificacao, cor, mensagem
    return SCORE_CLASSIFICATIONS[-1][1], SCORE_CLASSIFICATIONS[-1][2], SCORE_CLASSIFICATIONS[-1][3]


# ========== D1: Comprometimento com despesas fixas (0-25) ==========

D1_FAIXAS = [
    (50.0, 25),
    (60.0, 20),
    (70.0, 12),
    (80.0, 5),
]


def _calc_d1(renda: float, total_fixos: float) -> dict:
    """Calcula D1: comprometimento com despesas fixas."""
    if renda <= 0:
        return {"pontos": 0, "maximo": 25, "percentual_comprometimento": 0.0,
                "detalhe": "Sem renda cadastrada"}

    pct = total_fixos / renda * 100

    pontos = 0
    for limite, pts in D1_FAIXAS:
        if pct <= limite:
            pontos = pts
            break

    return {
        "pontos": pontos,
        "maximo": 25,
        "percentual_comprometimento": round(pct, 1),
        "detalhe": f"Gastos fixos consomem {round(pct, 1)}% da renda (ideal: até 50%)",
    }


# ========== D2: Pressao de parcelas (0-25) ==========

D2A_FAIXAS = [
    (15.0, 10),
    (25.0, 7),
    (35.0, 4),
    (50.0, 2),
]

D2B_FAIXAS = [
    (3, 5),
    (6, 3),
    (10, 1),
]


def _calc_d2(renda: float, installment_groups: list[dict], mes_atual: date) -> dict:
    """Calcula D2: pressao de parcelas com 4 subfatores."""
    if renda <= 0:
        return {"pontos": 0, "maximo": 25,
                "subfatores": {
                    "d2a_percentual": {"pontos": 0, "valor": 0.0},
                    "d2b_quantidade": {"pontos": 0, "valor": 0},
                    "d2c_pendentes": {"pontos": 0, "quantidade": 0},
                    "d2d_alivio": {"pontos": 0, "percentual_liberacao": 0.0},
                },
                "detalhe": "Sem renda cadastrada"}

    # Separar parcelas ativas de pendentes (0 de Y)
    ativas = []
    pendentes = []
    for group in installment_groups:
        installments = group.get("installments", [])
        num_paid = sum(1 for inst in installments if inst.status == ExpenseStatus.PAGO.value)
        if num_paid == 0 and group["status_geral"] != "Concluído":
            pendentes.append(group)
        elif group["status_geral"] == "Em andamento":
            ativas.append(group)

    # D2a: % da renda so em parcelas
    total_parcelas_mensal = sum(float(g["installments"][0].valor) for g in ativas if g["installments"])
    pct_parcelas = total_parcelas_mensal / renda * 100

    d2a = 0
    for limite, pts in D2A_FAIXAS:
        if pct_parcelas <= limite:
            d2a = pts
            break

    # D2b: quantidade de parcelas simultaneas
    qtd_ativas = len(ativas)
    d2b = 0
    for limite, pts in D2B_FAIXAS:
        if qtd_ativas <= limite:
            d2b = pts
            break

    # D2c: parcelas pendentes nao iniciadas
    qtd_pendentes = len(pendentes)
    d2c = -5 if qtd_pendentes > 0 else 0

    # D2d: alivio futuro proximo (parcelas encerrando em 3 meses)
    valor_liberado_3m = 0.0
    for group in ativas:
        installments = group.get("installments", [])
        if not installments:
            continue
        parcela_total = group["parcela_total"]
        num_paid = sum(1 for inst in installments if inst.status == ExpenseStatus.PAGO.value)

        if len(installments) >= parcela_total:
            parcelas_restantes = len([inst for inst in installments if inst.status != ExpenseStatus.PAGO.value])
        else:
            paid_nums = [inst.parcela_atual or 0 for inst in installments if inst.status == ExpenseStatus.PAGO.value]
            progresso = max(paid_nums) if paid_nums else 0
            parcelas_restantes = parcela_total - progresso

        if 0 < parcelas_restantes <= 3:
            valor_liberado_3m += float(installments[0].valor)

    pct_liberacao = valor_liberado_3m / renda * 100 if renda > 0 else 0
    if pct_liberacao >= 10:
        d2d = 5
    elif pct_liberacao >= 5:
        d2d = 3
    else:
        d2d = 0

    total = max(0, min(25, d2a + d2b + d2c + d2d))

    return {
        "pontos": total,
        "maximo": 25,
        "subfatores": {
            "d2a_percentual": {"pontos": d2a, "valor": round(pct_parcelas, 1)},
            "d2b_quantidade": {"pontos": d2b, "valor": qtd_ativas},
            "d2c_pendentes": {"pontos": d2c, "quantidade": qtd_pendentes},
            "d2d_alivio": {"pontos": d2d, "percentual_liberacao": round(pct_liberacao, 1)},
        },
        "detalhe": f"{qtd_ativas} parcelas ativas" + (f" com {qtd_pendentes} pendentes" if qtd_pendentes > 0 else "") + ". " + ("Pressão alta." if total < 10 else "Pressão controlada." if total < 20 else "Sem pressão significativa."),
    }


# ========== D3: Capacidade de poupanca (0-25) ==========

D3_FAIXAS = [
    (0.0, 0),    # ≤ 0%
    (5.0, 3),    # 0.1% – 4.9%
    (10.0, 8),   # 5% – 9.9%
    (15.0, 15),  # 10% – 14.9%
    (20.0, 20),  # 15% – 19.9%
]


def _calc_d3(renda: float, total_fixos: float, media_variaveis: float,
             dias_dados: int, dias_no_mes: int) -> dict:
    """Calcula D3: capacidade de poupanca."""
    if renda <= 0:
        return {"pontos": 0, "maximo": 25, "percentual_livre": 0.0,
                "estimativa_variaveis": False, "dias_dados_variaveis": 0,
                "detalhe": "Sem renda cadastrada"}

    saldo_livre = renda - total_fixos - media_variaveis
    pct_livre = saldo_livre / renda * 100

    if pct_livre >= 20:
        pontos = 25
    elif pct_livre <= 0:
        pontos = 0
    else:
        pontos = 0
        for limite, pts in D3_FAIXAS:
            if pct_livre <= limite:
                pontos = pts
                break
            pontos = pts  # Keep the last valid value
        # Check the thresholds properly
        if pct_livre > 0 and pct_livre < 5:
            pontos = 3
        elif pct_livre >= 5 and pct_livre < 10:
            pontos = 8
        elif pct_livre >= 10 and pct_livre < 15:
            pontos = 15
        elif pct_livre >= 15 and pct_livre < 20:
            pontos = 20

    estimativa = dias_dados < 30  # less than a full month of data

    return {
        "pontos": pontos,
        "maximo": 25,
        "percentual_livre": round(pct_livre, 1),
        "estimativa_variaveis": estimativa,
        "dias_dados_variaveis": dias_dados,
        "detalhe": f"Saldo livre {'estimado em' if estimativa else 'de'} {round(pct_livre, 1)}%" + (f" (baseado em {dias_dados} dias de dados)" if estimativa else ""),
    }


# ========== D4: Comportamento e disciplina (0-25) ==========

def _calc_d4(expenses: list[Expense], daily_expenses: list[DailyExpense],
             prev_comprometimento: float | None, installment_groups: list[dict],
             mes_atual: date) -> dict:
    """Calcula D4: comportamento e disciplina com 4 subfatores."""
    dias_no_mes = calendar.monthrange(mes_atual.year, mes_atual.month)[1]

    # D4a: Pontualidade nos pagamentos (0-10)
    total_expenses = len(expenses)
    if total_expenses > 0:
        em_dia = sum(1 for e in expenses if e.status != ExpenseStatus.ATRASADO.value)
        d4a = round(em_dia / total_expenses * 10)
    else:
        d4a = 10  # sem despesas = pontuacao maxima

    pct_em_dia = round(em_dia / total_expenses * 100, 1) if total_expenses > 0 else 100.0

    # D4b: Consistencia de registro de gastos diarios (0-5)
    dias_com_registro = len(set(de.data for de in daily_expenses))
    d4b = min(5, round(dias_com_registro / 20 * 5))

    # D4c: Tendencia mensal (0-5)
    primeiro_mes = prev_comprometimento is None
    if primeiro_mes:
        d4c = 3  # neutro
    else:
        # Calcular comprometimento atual
        renda_total = 0.0  # Will be computed externally; use expenses ratio as proxy
        # D4c needs the actual comprometimento percentual, which is passed in
        # prev_comprometimento is the % from the previous month
        # We need current month comprometimento - this will be computed in the main function
        # For now, D4c receives the difference directly
        d4c = 3  # placeholder, will be overridden

    # D4d: Disciplina de parcelamento (0-5)
    # Nova parcela longa (> 12x) criada no mes
    nova_parcela_longa = None
    d4d = 5  # assume disciplinado

    for group in installment_groups:
        if group["parcela_total"] <= 12:
            continue
        installments = group.get("installments", [])
        for inst in installments:
            if (inst.parcela_atual == 1
                    and hasattr(inst, 'created_at') and inst.created_at
                    and inst.created_at.year == mes_atual.year
                    and inst.created_at.month == mes_atual.month):
                nova_parcela_longa = group["nome"]
                valor_mensal = float(inst.valor)
                # Check against renda - will be passed from outside
                # For now mark as found
                d4d = 2  # default for "found but impact unknown"
                break
        if nova_parcela_longa:
            break

    return {
        "pontos": d4a + d4b + d4c + d4d,
        "maximo": 25,
        "subfatores": {
            "d4a_pontualidade": {"pontos": d4a, "percentual_em_dia": pct_em_dia},
            "d4b_consistencia": {"pontos": d4b, "dias_registro": dias_com_registro},
            "d4c_tendencia": {"pontos": d4c, "primeiro_mes": primeiro_mes},
            "d4d_disciplina": {"pontos": d4d, "nova_parcela_longa": nova_parcela_longa},
        },
        "detalhe": f"{'Pagamentos em dia' if d4a >= 8 else 'Algumas despesas atrasadas'}" + f", {'poucos' if d4b < 3 else 'bom número de'} dias de registro",
    }


# ========== Main Calculation ==========

def calculate_health_score(
    renda: float,
    expenses: list[Expense],
    daily_expenses: list[DailyExpense],
    installment_groups: list[dict],
    daily_expense_history: list[tuple[date, float]],
    prev_month_comprometimento: float | None,
    mes_atual: date,
) -> dict:
    """
    Calcula o score de saude financeira deterministico (0-100).

    Args:
        renda: total de receitas do mes
        expenses: despesas planejadas do mes (com status atualizado)
        daily_expenses: gastos diarios do mes
        installment_groups: grupos de parcelas do crud.get_installment_expenses_grouped()
        daily_expense_history: [(mes, total)] dos ultimos 3 meses para media de variaveis
        prev_month_comprometimento: % de comprometimento do mes anterior (None se primeiro mes)
        mes_atual: primeiro dia do mes de referencia

    Returns:
        dict com score total, dimensoes detalhadas, classificacao
    """
    # Edge case: sem renda
    if renda <= 0:
        return {
            "score": {
                "total": 0,
                "classificacao": "Crítica",
                "cor": "#C0392B",
                "mensagem": "Cadastre sua renda para calcular o score",
                "mensagem_contextual": "Cadastre sua renda para calcular o score de saúde financeira.",
                "mes_referencia": mes_atual.strftime("%Y-%m"),
            },
            "dimensoes": {
                "d1_comprometimento": {"pontos": 0, "maximo": 25, "percentual_comprometimento": 0.0, "detalhe": "Sem renda cadastrada"},
                "d2_parcelas": {"pontos": 0, "maximo": 25, "subfatores": {}, "detalhe": "Sem renda cadastrada"},
                "d3_poupanca": {"pontos": 0, "maximo": 25, "percentual_livre": 0.0, "estimativa_variaveis": False, "dias_dados_variaveis": 0, "detalhe": "Sem renda cadastrada"},
                "d4_comportamento": {"pontos": 0, "maximo": 25, "subfatores": {}, "detalhe": "Sem renda cadastrada"},
            },
        }

    # Calcular totais
    total_fixos = sum(float(e.valor) for e in expenses)
    dias_no_mes = calendar.monthrange(mes_atual.year, mes_atual.month)[1]

    # Media de variaveis (ultimos 3 meses ou projecao)
    if len(daily_expense_history) >= 3:
        media_variaveis = sum(total for _, total in daily_expense_history[-3:]) / 3
        dias_dados = dias_no_mes  # full data available
    else:
        # Projetar com base nos dados disponiveis do mes atual
        total_variaveis_atual = sum(float(de.valor) for de in daily_expenses)
        dias_registrados = len(set(de.data for de in daily_expenses))
        if dias_registrados > 0:
            media_variaveis = total_variaveis_atual * (dias_no_mes / dias_registrados)
        else:
            media_variaveis = 0.0
        dias_dados = dias_registrados

    # Edge case: sem despesas
    if not expenses and not daily_expenses and not installment_groups:
        return {
            "score": {
                "total": 100,
                "classificacao": "Excelente",
                "cor": "#1E8449",
                "mensagem": "Saúde financeira excepcional",
                "mensagem_contextual": "Sem despesas cadastradas. Score máximo.",
                "mes_referencia": mes_atual.strftime("%Y-%m"),
            },
            "dimensoes": {
                "d1_comprometimento": {"pontos": 25, "maximo": 25, "percentual_comprometimento": 0.0, "detalhe": "Sem despesas fixas"},
                "d2_parcelas": {"pontos": 25, "maximo": 25, "subfatores": {"d2a_percentual": {"pontos": 10, "valor": 0.0}, "d2b_quantidade": {"pontos": 5, "valor": 0}, "d2c_pendentes": {"pontos": 0, "quantidade": 0}, "d2d_alivio": {"pontos": 0, "percentual_liberacao": 0.0}}, "detalhe": "Sem parcelas ativas. Sem pressão significativa."},
                "d3_poupanca": {"pontos": 25, "maximo": 25, "percentual_livre": 100.0, "estimativa_variaveis": False, "dias_dados_variaveis": 0, "detalhe": "Saldo livre de 100.0%"},
                "d4_comportamento": {"pontos": 25, "maximo": 25, "subfatores": {"d4a_pontualidade": {"pontos": 10, "percentual_em_dia": 100.0}, "d4b_consistencia": {"pontos": 0, "dias_registro": 0}, "d4c_tendencia": {"pontos": 3, "primeiro_mes": True}, "d4d_disciplina": {"pontos": 5, "nova_parcela_longa": None}}, "detalhe": "Pagamentos em dia, poucos dias de registro"},
            },
        }

    # D1: Comprometimento
    d1 = _calc_d1(renda, total_fixos)

    # D2: Pressao de parcelas
    active_groups = [g for g in installment_groups if g.get("installments")]
    d2 = _calc_d2(renda, active_groups, mes_atual)

    # D3: Capacidade de poupanca
    d3 = _calc_d3(renda, total_fixos, media_variaveis, dias_dados, dias_no_mes)

    # D4: Comportamento e disciplina
    # Primeiro calcular comprometimento atual para D4c
    comprometimento_atual = (total_fixos + media_variaveis) / renda * 100 if renda > 0 else 0
    d4 = _calc_d4(expenses, daily_expenses, prev_month_comprometimento, active_groups, mes_atual)

    # Override D4c with proper trend calculation
    if prev_month_comprometimento is not None:
        diff = prev_month_comprometimento - comprometimento_atual
        if diff >= 3:
            d4c_pontos = 5
        elif diff > 0:
            d4c_pontos = 3
        elif abs(diff) <= 0.1:
            d4c_pontos = 2
        else:
            d4c_pontos = 0
        # Recalculate D4 total with corrected D4c
        old_d4c = d4["subfatores"]["d4c_tendencia"]["pontos"]
        d4["subfatores"]["d4c_tendencia"]["pontos"] = d4c_pontos
        d4["subfatores"]["d4c_tendencia"]["primeiro_mes"] = False
        d4["pontos"] = d4["pontos"] - old_d4c + d4c_pontos

    # D4d: refine with renda info for new long installment
    for group in active_groups:
        if group["parcela_total"] <= 12:
            continue
        installments = group.get("installments", [])
        for inst in installments:
            if (inst.parcela_atual == 1
                    and hasattr(inst, 'created_at') and inst.created_at
                    and inst.created_at.year == mes_atual.year
                    and inst.created_at.month == mes_atual.month):
                valor_mensal = float(inst.valor)
                pct_renda = valor_mensal / renda * 100 if renda > 0 else 100
                if pct_renda >= 5:
                    new_d4d = 0
                else:
                    new_d4d = 2
                old_d4d = d4["subfatores"]["d4d_disciplina"]["pontos"]
                d4["subfatores"]["d4d_disciplina"]["pontos"] = new_d4d
                d4["pontos"] = d4["pontos"] - old_d4d + new_d4d
                break
        break

    # Total
    score_total = d1["pontos"] + d2["pontos"] + d3["pontos"] + d4["pontos"]
    score_total = max(0, min(100, score_total))

    classificacao, cor, mensagem = classify_score(score_total)

    # Mensagem contextual baseada na dimensao de menor pontuacao
    dimensoes_ranking = [
        ("d1_comprometimento", d1["pontos"], 25),
        ("d2_parcelas", d2["pontos"], 25),
        ("d3_poupanca", d3["pontos"], 25),
        ("d4_comportamento", d4["pontos"], 25),
    ]
    pior_dim = min(dimensoes_ranking, key=lambda x: x[1] / x[2])
    mensagem_contextual = _build_contextual_message(pior_dim[0], d1, d2, d3, d4, active_groups)

    return {
        "score": {
            "total": score_total,
            "classificacao": classificacao,
            "cor": cor,
            "mensagem": mensagem,
            "mensagem_contextual": mensagem_contextual,
            "mes_referencia": mes_atual.strftime("%Y-%m"),
        },
        "dimensoes": {
            "d1_comprometimento": d1,
            "d2_parcelas": d2,
            "d3_poupanca": d3,
            "d4_comportamento": d4,
        },
    }


def _build_contextual_message(dim_key: str, d1: dict, d2: dict, d3: dict, d4: dict,
                               installment_groups: list[dict]) -> str:
    """Gera mensagem contextual baseada na dimensao de menor pontuacao."""
    if dim_key == "d1_comprometimento":
        return f"Gastos fixos consomem {d1['percentual_comprometimento']}% da renda. Revisar despesas fixas pode melhorar seu score."
    elif dim_key == "d2_parcelas":
        # Find parcela encerrando em breve
        for g in installment_groups:
            installments = g.get("installments", [])
            if not installments:
                continue
            num_paid = sum(1 for i in installments if i.status == ExpenseStatus.PAGO.value)
            parcela_total = g["parcela_total"]
            restantes = parcela_total - num_paid
            if 0 < restantes <= 3:
                return f"Sua principal oportunidade: reduzir a pressão de parcelas. O {g['nome']} termina em breve."
        return "Sua principal oportunidade: reduzir a pressão de parcelas."
    elif dim_key == "d3_poupanca":
        return f"Seu saldo livre está em {d3['percentual_livre']}%. Revisar gastos variáveis pode abrir espaço."
    elif dim_key == "d4_comportamento":
        if d4["subfatores"]["d4a_pontualidade"]["pontos"] < 8:
            return "Manter os pagamentos em dia é a forma mais rápida de subir o score."
        return "Registrar gastos diários com mais frequência melhora sua visibilidade e seu score."
    return ""


# ========== Conservative Scenario ==========

def calculate_conservative_score(
    score_data: dict,
    installment_groups: list[dict],
    renda: float,
) -> dict | None:
    """
    Calcula score conservador incluindo parcelas pendentes (0 de Y) como ativas.
    Retorna None se nao ha parcelas pendentes.
    """
    # Find pending installments (0 pagas)
    pending = []
    for group in installment_groups:
        installments = group.get("installments", [])
        num_paid = sum(1 for inst in installments if inst.status == ExpenseStatus.PAGO.value)
        if num_paid == 0 and group["status_geral"] != "Concluído" and installments:
            valor_mensal = float(installments[0].valor)
            pending.append({
                "descricao": group["nome"],
                "valor_estimado_mensal": round(valor_mensal, 2),
                "total_parcelas": group["parcela_total"],
            })

    if not pending:
        return None

    # Recalculate with pending as active
    total_pendentes_mensal = sum(p["valor_estimado_mensal"] for p in pending)

    # Get current D1 and D2 data
    d1_data = score_data["dimensoes"]["d1_comprometimento"]
    d2_data = score_data["dimensoes"]["d2_parcelas"]
    d3_data = score_data["dimensoes"]["d3_poupanca"]
    d4_data = score_data["dimensoes"]["d4_comportamento"]

    # Recalculate D1 with added commitment
    current_fixos = d1_data["percentual_comprometimento"] / 100 * renda if renda > 0 else 0
    new_fixos = current_fixos + total_pendentes_mensal
    new_d1 = _calc_d1(renda, new_fixos)

    # Recalculate D3 with reduced free balance
    new_pct_livre = d3_data["percentual_livre"] - (total_pendentes_mensal / renda * 100 if renda > 0 else 0)
    if new_pct_livre >= 20:
        new_d3_pontos = 25
    elif new_pct_livre <= 0:
        new_d3_pontos = 0
    elif new_pct_livre < 5:
        new_d3_pontos = 3
    elif new_pct_livre < 10:
        new_d3_pontos = 8
    elif new_pct_livre < 15:
        new_d3_pontos = 15
    else:
        new_d3_pontos = 20

    # D2 and D4 stay the same
    new_total = new_d1["pontos"] + d2_data["pontos"] + new_d3_pontos + d4_data["pontos"]
    new_total = max(0, min(100, new_total))
    classificacao, _, _ = classify_score(new_total)

    new_comprometimento = round(new_fixos / renda * 100, 1) if renda > 0 else 0

    return {
        "score": new_total,
        "classificacao": classificacao,
        "parcelas_pendentes": pending,
        "impacto": f"Se ativadas, comprometimento sobe para ~{new_comprometimento}%",
    }


# ========== Actions Generator ==========

def generate_actions(
    score_data: dict,
    renda: float,
    expenses: list[Expense],
    daily_expenses: list[DailyExpense],
    installment_groups: list[dict],
) -> list[dict]:
    """
    Gera ate 3 acoes sugeridas ordenadas por impacto estimado no score.
    Identifica dimensoes com menor pontuacao e gera acoes especificas.
    """
    if renda <= 0:
        return []

    dimensoes = score_data["dimensoes"]
    actions = []

    # Rank dimensions by relative score (pontos/maximo)
    dim_ranking = [
        ("d1_comprometimento", dimensoes["d1_comprometimento"]["pontos"], 25),
        ("d2_parcelas", dimensoes["d2_parcelas"]["pontos"], 25),
        ("d3_poupanca", dimensoes["d3_poupanca"]["pontos"], 25),
        ("d4_comportamento", dimensoes["d4_comportamento"]["pontos"], 25),
    ]
    dim_ranking.sort(key=lambda x: x[1] / x[2])

    for dim_key, pontos, maximo in dim_ranking:
        if len(actions) >= 3:
            break

        ratio = pontos / maximo
        if ratio >= 0.8:  # Already good, skip
            continue

        if dim_key == "d1_comprometimento":
            # Suggest reviewing fixed expenses
            pct = dimensoes["d1_comprometimento"]["percentual_comprometimento"]
            if pct > 50:
                impacto = _estimate_d1_impact(renda, expenses, dimensoes)
                actions.append({
                    "prioridade": len(actions) + 1,
                    "dimensao_alvo": "d1_comprometimento",
                    "descricao": f"Revisar despesas fixas não essenciais. Comprometimento atual: {pct}% (ideal: até 50%).",
                    "impacto_estimado": impacto,
                    "tipo": "redução",
                })

        elif dim_key == "d2_parcelas":
            # Find parcelas encerrando em breve
            for group in installment_groups:
                installments = group.get("installments", [])
                if not installments:
                    continue
                num_paid = sum(1 for i in installments if i.status == ExpenseStatus.PAGO.value)
                restantes = group["parcela_total"] - num_paid
                if 0 < restantes <= 3:
                    valor = float(installments[0].valor)
                    actions.append({
                        "prioridade": len(actions) + 1,
                        "dimensao_alvo": "d2_parcelas",
                        "descricao": f"O {group['nome']} termina em breve. Redirecionar R$ {valor:.0f}/mês para poupança.",
                        "impacto_estimado": min(5, 25 - pontos),
                        "tipo": "oportunidade",
                    })
                    break

            # Check for pending installments
            subfatores = dimensoes["d2_parcelas"].get("subfatores", {})
            if subfatores.get("d2c_pendentes", {}).get("quantidade", 0) > 0:
                for group in installment_groups:
                    installments = group.get("installments", [])
                    num_paid = sum(1 for i in installments if i.status == ExpenseStatus.PAGO.value)
                    if num_paid == 0 and group["status_geral"] != "Concluído" and installments:
                        actions.append({
                            "prioridade": len(actions) + 1,
                            "dimensao_alvo": "d2_parcelas",
                            "descricao": f"Atenção: {group['nome']} ainda não iniciou. Quando ativar, comprometimento aumenta.",
                            "impacto_estimado": 0,
                            "tipo": "alerta",
                        })
                        break

        elif dim_key == "d3_poupanca":
            pct_livre = dimensoes["d3_poupanca"]["percentual_livre"]
            if pct_livre < 20:
                actions.append({
                    "prioridade": len(actions) + 1,
                    "dimensao_alvo": "d3_poupanca",
                    "descricao": f"Saldo livre em {pct_livre}%. Revisar gastos variáveis pode aumentar sua margem.",
                    "impacto_estimado": min(5, 25 - pontos),
                    "tipo": "redução",
                })

        elif dim_key == "d4_comportamento":
            subfatores = dimensoes["d4_comportamento"].get("subfatores", {})

            if subfatores.get("d4a_pontualidade", {}).get("pontos", 10) < 8:
                atrasadas = sum(1 for e in expenses if e.status == ExpenseStatus.ATRASADO.value)
                actions.append({
                    "prioridade": len(actions) + 1,
                    "dimensao_alvo": "d4_comportamento",
                    "descricao": f"Pagar {atrasadas} despesas atrasadas melhora seu score imediatamente.",
                    "impacto_estimado": min(5, 25 - pontos),
                    "tipo": "ação",
                })
            elif subfatores.get("d4b_consistencia", {}).get("pontos", 5) < 3:
                actions.append({
                    "prioridade": len(actions) + 1,
                    "dimensao_alvo": "d4_comportamento",
                    "descricao": "Registrar gastos diários com mais frequência. Meta: 15+ dias no mês.",
                    "impacto_estimado": min(3, 25 - pontos),
                    "tipo": "hábito",
                })

    # Sort by impact
    actions.sort(key=lambda a: a["impacto_estimado"], reverse=True)

    # Re-number priorities
    for i, action in enumerate(actions):
        action["prioridade"] = i + 1

    return actions[:3]


def _estimate_d1_impact(renda: float, expenses: list[Expense], dimensoes: dict) -> int:
    """Estima impacto de reduzir comprometimento em 5 p.p."""
    current_pct = dimensoes["d1_comprometimento"]["percentual_comprometimento"]
    target_pct = current_pct - 5
    current_pontos = dimensoes["d1_comprometimento"]["pontos"]

    # Recalculate D1 with reduced %
    new_fixos = target_pct / 100 * renda
    new_d1 = _calc_d1(renda, new_fixos)
    return max(0, new_d1["pontos"] - current_pontos)
