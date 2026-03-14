import calendar
import logging
from datetime import date

from sqlalchemy.orm import Session

from collections import defaultdict

from app import crud
from app.models import Expense, ExpenseStatus, Income

logger = logging.getLogger(__name__)


def get_next_month(current: date) -> date:
    """Dado um mes_referencia (1o dia do mes), retorna 1o dia do proximo mes."""
    if current.month == 12:
        return date(current.year + 1, 1, 1)
    return date(current.year, current.month + 1, 1)


def get_previous_month(current: date) -> date:
    """Dado um mes_referencia (1o dia do mes), retorna 1o dia do mes anterior."""
    if current.month == 1:
        return date(current.year - 1, 12, 1)
    return date(current.year, current.month - 1, 1)


def adjust_vencimento_to_month(original_date: date, target_mes: date) -> date:
    """
    Move uma data para o mes-alvo mantendo o mesmo dia.
    Se o dia nao existe no mes-alvo (ex: 31 jan -> fev), clamp para o ultimo dia.
    """
    last_day = calendar.monthrange(target_mes.year, target_mes.month)[1]
    day = min(original_date.day, last_day)
    return date(target_mes.year, target_mes.month, day)


def apply_status_auto_detection(
    expenses: list[Expense], today: date
) -> list[Expense]:
    """
    RF-05: Para despesas com status "Pendente" e vencimento < hoje,
    marca como "Atrasado". Modifica as instancias in-place.
    O chamador decide se persiste as mudancas.
    """
    for expense in expenses:
        if (
            expense.status == ExpenseStatus.PENDENTE.value
            and expense.vencimento < today
        ):
            expense.status = ExpenseStatus.ATRASADO.value
    return expenses


def generate_month_data(db: Session, target_mes: date, user_id: str) -> bool:
    """
    RF-06: Algoritmo de Transicao de Mes com replicacao incremental.
    (CR-002: user_id para isolamento)

    Chamado quando o usuario navega para qualquer mes.
    Olha os dados do mes anterior DO MESMO USUARIO e replica entradas faltantes
    para target_mes, usando origem_id para deduplicacao por-item.

    Retorna True se novos dados foram gerados, False se nada foi replicado.

    Algoritmo:
    1. Buscar despesas e receitas do usuario no mes anterior
    2. Para cada despesa que deveria replicar:
       - Checar se ja existe replica no mes-alvo (por origem_id)
       - Se nao existe, criar replica
    3. Mesma logica para receitas
    4. Novas entradas recebem status=Pendente, novos UUIDs, origem_id=id da origem.
    """
    logger.info(
        "generate_month_data called: target_mes=%s, user_id=%s",
        target_mes, user_id,
    )

    # Passo 1: Buscar dados do usuario no mes anterior
    prev_mes = get_previous_month(target_mes)
    prev_expenses = crud.get_expenses_by_month(db, prev_mes, user_id)
    prev_incomes = crud.get_incomes_by_month(db, prev_mes, user_id)
    logger.info(
        "Previous month %s: %d expenses, %d incomes",
        prev_mes, len(prev_expenses), len(prev_incomes),
    )

    if not prev_expenses and not prev_incomes:
        logger.info("SKIP: Previous month has no data, returning False")
        return False

    # Passo 2: Replicar despesas (incremental, com deduplicacao por origem_id)
    replicated_count = 0
    for exp in prev_expenses:
        if exp.parcela_atual is not None and exp.parcela_total is not None:
            # Despesa parcelada
            if exp.parcela_atual < exp.parcela_total:
                if crud.expense_replica_exists(db, target_mes, user_id, exp.id):
                    logger.debug("SKIP already replicated: '%s'", exp.nome)
                    continue
                if crud.expense_installment_exists(db, target_mes, user_id, exp.nome, exp.parcela_atual + 1, exp.parcela_total):
                    logger.debug("SKIP already upfront-created: '%s'", exp.nome)
                    continue
                logger.info(
                    "REPLICATE installment: '%s' parcela %d/%d -> %d/%d",
                    exp.nome, exp.parcela_atual, exp.parcela_total,
                    exp.parcela_atual + 1, exp.parcela_total,
                )
                new_exp = Expense(
                    user_id=user_id,
                    mes_referencia=target_mes,
                    nome=exp.nome,
                    categoria=exp.categoria,  # CR-016
                    subcategoria=exp.subcategoria,  # CR-016
                    valor=exp.valor,
                    vencimento=adjust_vencimento_to_month(
                        exp.vencimento, target_mes
                    ),
                    parcela_atual=exp.parcela_atual + 1,
                    parcela_total=exp.parcela_total,
                    recorrente=exp.recorrente,
                    origem_id=exp.id,
                    status=ExpenseStatus.PENDENTE.value,
                )
                db.add(new_exp)
                replicated_count += 1
            else:
                logger.debug(
                    "SKIP last installment: '%s' parcela %d/%d",
                    exp.nome, exp.parcela_atual, exp.parcela_total,
                )
        else:
            # Despesa sem parcela
            if exp.recorrente:
                if crud.expense_replica_exists(db, target_mes, user_id, exp.id):
                    logger.debug("SKIP already replicated: '%s'", exp.nome)
                    continue
                logger.info("REPLICATE recurring: '%s'", exp.nome)
                new_exp = Expense(
                    user_id=user_id,
                    mes_referencia=target_mes,
                    nome=exp.nome,
                    categoria=exp.categoria,  # CR-016
                    subcategoria=exp.subcategoria,  # CR-016
                    valor=exp.valor,
                    vencimento=adjust_vencimento_to_month(
                        exp.vencimento, target_mes
                    ),
                    parcela_atual=None,
                    parcela_total=None,
                    recorrente=True,
                    origem_id=exp.id,
                    status=ExpenseStatus.PENDENTE.value,
                )
                db.add(new_exp)
                replicated_count += 1
            else:
                logger.debug(
                    "SKIP non-recurring: '%s' (recorrente=%s)",
                    exp.nome, exp.recorrente,
                )

    # Passo 3: Replicar receitas (incremental, com deduplicacao por origem_id)
    replicated_incomes = 0
    for inc in prev_incomes:
        if inc.recorrente:
            if crud.income_replica_exists(db, target_mes, user_id, inc.id):
                logger.debug("SKIP already replicated income: '%s'", inc.nome)
                continue
            logger.info("REPLICATE income: '%s'", inc.nome)
            new_inc = Income(
                user_id=user_id,
                mes_referencia=target_mes,
                nome=inc.nome,
                valor=inc.valor,
                data=(
                    adjust_vencimento_to_month(inc.data, target_mes)
                    if inc.data
                    else None
                ),
                recorrente=True,
                origem_id=inc.id,
            )
            db.add(new_inc)
            replicated_incomes += 1
        else:
            logger.debug("SKIP non-recurring income: '%s'", inc.nome)

    if replicated_count > 0 or replicated_incomes > 0:
        logger.info(
            "Replication complete: %d expenses, %d incomes replicated for %s",
            replicated_count, replicated_incomes, target_mes,
        )
        db.commit()
        return True

    logger.info("No new items to replicate for %s", target_mes)
    return False


def get_monthly_summary(db: Session, mes_referencia: date, user_id: str) -> dict:
    """
    Constroi a visao mensal completa para um usuario especifico. (CR-002: user_id)
    Passos:
    1. Tenta gerar dados do mes se vazio (RF-06)
    2. Busca despesas e receitas do usuario
    3. Aplica auto-deteccao de status (RF-05)
    4. Calcula totalizadores (RF-04)
    """
    # Passo 1: Auto-gerar se necessario (escopo por usuario)
    generate_month_data(db, mes_referencia, user_id)  # CR-002

    # Passo 2: Buscar dados do usuario
    expenses = crud.get_expenses_by_month(db, mes_referencia, user_id)  # CR-002
    incomes = crud.get_incomes_by_month(db, mes_referencia, user_id)  # CR-002

    # Passo 3: Auto-detectar status de atraso
    today = date.today()
    apply_status_auto_detection(expenses, today)
    db.commit()  # Persiste mudancas de status

    # Passo 4: Calcular totalizadores
    total_despesas = sum(float(e.valor) for e in expenses)
    total_receitas = sum(float(i.valor) for i in incomes)

    # Passo 5: Totalizadores por status (CR-004)
    total_pago = sum(float(e.valor) for e in expenses if e.status == ExpenseStatus.PAGO.value)
    total_pendente = sum(float(e.valor) for e in expenses if e.status == ExpenseStatus.PENDENTE.value)
    total_atrasado = sum(float(e.valor) for e in expenses if e.status == ExpenseStatus.ATRASADO.value)

    return {
        "mes_referencia": mes_referencia,
        "total_despesas": round(total_despesas, 2),
        "total_receitas": round(total_receitas, 2),
        "saldo_livre": round(total_receitas - total_despesas, 2),
        "total_pago": round(total_pago, 2),
        "total_pendente": round(total_pendente, 2),
        "total_atrasado": round(total_atrasado, 2),
        "expenses": expenses,
        "incomes": incomes,
    }


def _build_category_breakdown(items: list, category_attr: str = "categoria") -> list[dict]:
    """Agrupa itens por categoria e calcula percentuais. Retorna lista ordenada por total desc."""
    cat_map: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "count": 0})
    for item in items:
        cat = getattr(item, category_attr, None) or "Outros"
        cat_map[cat]["total"] += float(item.valor)
        cat_map[cat]["count"] += 1

    total_geral = sum(v["total"] for v in cat_map.values())

    result = []
    for cat, data in cat_map.items():
        pct = (data["total"] / total_geral * 100) if total_geral > 0 else 0
        result.append({
            "categoria": cat,
            "total": round(data["total"], 2),
            "percentual": round(pct, 1),
            "count": data["count"],
        })

    return sorted(result, key=lambda x: x["total"], reverse=True)


def get_dashboard_data(db: Session, mes_referencia: date, user_id: str) -> dict:
    """
    CR-019: Constroi dados completos do dashboard para um mes.
    1. Dados do mes atual (com auto-generate e status detection via get_monthly_summary)
    2. Gastos diarios do mes
    3. Parcelas futuras
    4. Breakdown por categoria (separados: planejadas e diarios)
    5. Evolucao 6 meses (queries agregadas, sem auto-generate)
    """
    # 1. Dados do mes atual (triggers RF-05 e RF-06)
    monthly = get_monthly_summary(db, mes_referencia, user_id)
    expenses = monthly["expenses"]
    total_despesas_planejadas = monthly["total_despesas"]
    total_receitas = monthly["total_receitas"]

    # 2. Gastos diarios do mes
    daily_expenses = crud.get_daily_expenses_by_month(db, mes_referencia, user_id)
    total_gastos_diarios = round(sum(float(de.valor) for de in daily_expenses), 2)

    # 3. Totais combinados
    total_despesas_geral = round(total_despesas_planejadas + total_gastos_diarios, 2)
    saldo_livre = round(total_receitas - total_despesas_geral, 2)
    pct_comprometimento = round(
        (total_despesas_geral / total_receitas * 100) if total_receitas > 0 else 0, 1
    )

    # 4. Parcelas futuras (valor restante de todas as parcelas ativas)
    installments_data = crud.get_installment_expenses_grouped(db, user_id)
    total_parcelas_futuras = round(
        sum(g["valor_restante"] for g in installments_data["groups"] if g["status_geral"] == "Em andamento"),
        2
    )

    # 5. Breakdown por categoria — SEPARADOS
    categorias_planejadas = _build_category_breakdown(expenses)
    categorias_diarios = _build_category_breakdown(daily_expenses)

    # 6. Evolucao 6 meses (atual + 5 anteriores) — queries agregadas leves
    evolucao = []
    current_mes = mes_referencia
    for _ in range(6):
        if current_mes == mes_referencia:
            # Mes atual: usar dados ja calculados
            ev_despesas = total_despesas_planejadas
            ev_receitas = total_receitas
            ev_diarios = total_gastos_diarios
        else:
            # Meses anteriores: queries agregadas (sem auto-generate)
            ev_despesas = crud.get_expense_total_by_month(db, current_mes, user_id)
            ev_receitas = crud.get_income_total_by_month(db, current_mes, user_id)
            ev_diarios = crud.get_daily_expense_total_by_month(db, current_mes, user_id)

        ev_saldo = round(ev_receitas - ev_despesas - ev_diarios, 2)
        evolucao.append({
            "mes_referencia": current_mes,
            "total_despesas": ev_despesas,
            "total_receitas": ev_receitas,
            "total_gastos_diarios": ev_diarios,
            "saldo_livre": ev_saldo,
        })
        current_mes = get_previous_month(current_mes)

    # Inverter para ordem cronologica (mais antigo primeiro)
    evolucao.reverse()

    return {
        "mes_referencia": mes_referencia,
        "total_receitas": total_receitas,
        "total_despesas_planejadas": total_despesas_planejadas,
        "total_gastos_diarios": total_gastos_diarios,
        "total_despesas_geral": total_despesas_geral,
        "saldo_livre": saldo_livre,
        "percentual_comprometimento": pct_comprometimento,
        "total_parcelas_futuras": total_parcelas_futuras,
        "total_pago": monthly["total_pago"],
        "total_pendente": monthly["total_pendente"],
        "total_atrasado": monthly["total_atrasado"],
        "categorias_planejadas": categorias_planejadas,
        "categorias_diarios": categorias_diarios,
        "evolucao": evolucao,
    }


def get_installment_projection(db: Session, user_id: str, months: int = 12) -> dict:
    """
    CR-021: Calcula projecao de parcelas futuras para os proximos N meses.
    Retorna resumo com KPIs, projecao mensal e lista de parcelas ativas.

    Reutiliza crud.get_installment_expenses_grouped() para dados de parcelas
    e crud.get_income_total_by_month() para renda do mes atual.
    """
    today = date.today()
    mes_atual = date(today.year, today.month, 1)

    # 1. Buscar grupos de parcelas
    installments_data = crud.get_installment_expenses_grouped(db, user_id)
    groups = installments_data["groups"]

    # 2. Buscar renda do mes atual
    renda_atual = crud.get_income_total_by_month(db, mes_atual, user_id)

    # 3. Extrair info de cada grupo ativo para projecao
    parcelas_info = []
    for group in groups:
        if group["status_geral"] != "Em andamento":
            continue

        installments = group["installments"]
        if not installments:
            continue

        # Encontrar maior parcela_atual no grupo
        max_parcela_atual = max(
            (inst.parcela_atual or 0) for inst in installments
        )
        parcela_total = group["parcela_total"]

        # Valor mensal = valor da primeira parcela (todas tem mesmo valor)
        valor_mensal = float(installments[0].valor)

        # CR-022: Fallback quando parcela_atual nao esta preenchido —
        # inferir progresso contando parcelas com status PAGO
        if max_parcela_atual == 0:
            from app.models import ExpenseStatus
            num_paid = sum(
                1 for inst in installments
                if inst.status == ExpenseStatus.PAGO.value
            )
            max_parcela_atual = num_paid

        # Calcular parcelas restantes e mes de termino
        if max_parcela_atual == 0:
            # Pendente (nao iniciada, nenhuma parcela paga)
            parcelas_restantes = parcela_total
            mes_termino = None
            status_badge = "Pendente"
        else:
            parcelas_restantes = parcela_total - max_parcela_atual
            if parcelas_restantes <= 0:
                continue  # Ja concluida
            # Calcular mes de termino
            mes_termino = mes_atual
            for _ in range(parcelas_restantes):
                mes_termino = get_next_month(mes_termino)
            status_badge = "Encerrando" if parcelas_restantes <= 2 else "Ativa"

        parcelas_info.append({
            "nome": group["nome"],
            "valor_mensal": valor_mensal,
            "parcela_atual": max_parcela_atual,
            "parcela_total": parcela_total,
            "parcelas_restantes": parcelas_restantes,
            "mes_termino": mes_termino,
            "status_badge": status_badge,
        })

    # 4. Construir projecao mensal
    projecao_mensal = []
    prev_total = None

    for offset in range(months):
        mes_projecao = mes_atual
        for _ in range(offset):
            mes_projecao = get_next_month(mes_projecao)

        # Parcelas ativas neste mes (excluir pendentes e ja encerradas)
        ativas_nomes = []
        total_comprometido = 0.0
        encerrando_nomes = []

        for p in parcelas_info:
            if p["status_badge"] == "Pendente":
                continue  # Pendentes nao contam no comprometido

            # A parcela esta ativa se ainda tem parcelas restantes > offset
            if p["parcelas_restantes"] > offset:
                ativas_nomes.append(p["nome"])
                total_comprometido += p["valor_mensal"]

                # Encerrando neste mes especifico?
                if p["parcelas_restantes"] == offset + 1:
                    encerrando_nomes.append(p["nome"])

        total_comprometido = round(total_comprometido, 2)
        valor_liberado = round(prev_total - total_comprometido, 2) if prev_total is not None else 0.0
        pct = round((total_comprometido / renda_atual * 100) if renda_atual > 0 else 0, 1)

        projecao_mensal.append({
            "mes": mes_projecao,
            "total_comprometido": total_comprometido,
            "parcelas_ativas": len(ativas_nomes),
            "parcelas_encerrando": encerrando_nomes,
            "valor_liberado": valor_liberado,
            "percentual_comprometimento": pct,
        })
        prev_total = total_comprometido

    # 5. Calcular KPIs de resumo
    total_comprometido_mes_atual = projecao_mensal[0]["total_comprometido"] if projecao_mensal else 0.0
    qtd_ativas = len([p for p in parcelas_info if p["status_badge"] != "Pendente"])

    # Total restante = soma de (parcelas_restantes * valor_mensal) para todas as parcelas nao-pendentes
    total_restante = round(
        sum(p["parcelas_restantes"] * p["valor_mensal"] for p in parcelas_info if p["status_badge"] != "Pendente"),
        2
    )

    # Proxima a encerrar (menor mes_termino entre as nao-pendentes)
    nao_pendentes_com_termino = [
        p for p in parcelas_info
        if p["status_badge"] != "Pendente" and p["mes_termino"] is not None
    ]
    proxima_a_encerrar = None
    if nao_pendentes_com_termino:
        mais_proxima = min(nao_pendentes_com_termino, key=lambda p: p["mes_termino"])
        proxima_a_encerrar = {
            "nome": mais_proxima["nome"],
            "mes_termino": mais_proxima["mes_termino"],
        }

    # Liberacao proximos 3 meses = soma de valor_liberado nos meses 1, 2, 3
    liberacao_3m = round(
        sum(projecao_mensal[i]["valor_liberado"] for i in range(1, min(4, len(projecao_mensal)))),
        2
    )

    pct_renda = round(
        (total_comprometido_mes_atual / renda_atual * 100) if renda_atual > 0 else 0, 1
    )

    return {
        "total_comprometido_mes_atual": total_comprometido_mes_atual,
        "total_restante_todas_parcelas": total_restante,
        "qtd_parcelas_ativas": qtd_ativas,
        "proxima_a_encerrar": proxima_a_encerrar,
        "liberacao_proximos_3_meses": liberacao_3m,
        "percentual_renda_comprometida": pct_renda,
        "renda_atual": renda_atual,
        "projecao_mensal": projecao_mensal,
        "parcelas": parcelas_info,
    }


def get_daily_expenses_monthly_summary(db: Session, mes_referencia: date, user_id: str) -> dict:
    """
    CR-005: Constroi a visao mensal de gastos diarios, agrupados por dia.
    Retorna lista de dias com subtotais e total do mes.
    """
    daily_expenses = crud.get_daily_expenses_by_month(db, mes_referencia, user_id)

    # Agrupar por dia
    days_map: dict[date, list] = {}
    for de in daily_expenses:
        day = de.data
        if day not in days_map:
            days_map[day] = []
        days_map[day].append(de)

    # Construir sumarios por dia, ordenados por data desc (mais recente primeiro)
    dias = []
    for day in sorted(days_map.keys(), reverse=True):
        gastos = days_map[day]
        subtotal = sum(float(g.valor) for g in gastos)
        dias.append({
            "data": day,
            "gastos": gastos,
            "subtotal": round(subtotal, 2),
        })

    total_mes = sum(d["subtotal"] for d in dias)

    return {
        "mes_referencia": mes_referencia,
        "total_mes": round(total_mes, 2),
        "dias": dias,
    }
