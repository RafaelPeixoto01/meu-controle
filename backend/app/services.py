import calendar
import logging
from datetime import date

from sqlalchemy.orm import Session

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
