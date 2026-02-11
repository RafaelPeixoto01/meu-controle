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
    RF-06: Algoritmo de Transicao de Mes. (CR-002: user_id para isolamento)

    Chamado quando o usuario navega para um mes sem dados.
    Olha os dados do mes anterior DO MESMO USUARIO e gera entradas para target_mes
    seguindo as regras de replicacao.

    Retorna True se dados foram gerados, False se o mes-alvo ja tinha dados
    ou o mes anterior nao tinha dados (nada a replicar).

    Algoritmo:
    1. Checar se target_mes ja tem dados do usuario → se sim, return False (idempotente)
    2. Buscar despesas e receitas do usuario no mes anterior
    3. Para cada despesa:
       a. Tem parcela (parcela_atual e parcela_total preenchidos)?
          - Se parcela_atual < parcela_total: replicar com parcela_atual + 1
          - Se parcela_atual == parcela_total: NAO replicar (ultima parcela)
       b. Nao tem parcela?
          - Se recorrente == True: replicar com mesmos dados
          - Se recorrente == False: NAO replicar (despesa avulsa)
    4. Para cada receita:
       - Se recorrente == True: replicar
       - Se recorrente == False: NAO replicar
    5. Todas as novas entradas recebem status = Pendente, novos UUIDs e user_id do usuario.
    """
    logger.info(
        "generate_month_data called: target_mes=%s, user_id=%s",
        target_mes, user_id,
    )

    # Passo 1: Check de idempotencia (escopo por usuario)
    existing_expenses = crud.count_expenses_by_month(db, target_mes, user_id)  # CR-002
    existing_incomes = len(crud.get_incomes_by_month(db, target_mes, user_id))  # CR-002
    logger.info(
        "Idempotency check: target has %d expenses, %d incomes",
        existing_expenses, existing_incomes,
    )
    if existing_expenses > 0 or existing_incomes > 0:
        logger.info("SKIP: Target month already has data, returning False")
        return False

    # Passo 2: Buscar dados do usuario no mes anterior
    prev_mes = get_previous_month(target_mes)
    prev_expenses = crud.get_expenses_by_month(db, prev_mes, user_id)  # CR-002
    prev_incomes = crud.get_incomes_by_month(db, prev_mes, user_id)  # CR-002
    logger.info(
        "Previous month %s: %d expenses, %d incomes",
        prev_mes, len(prev_expenses), len(prev_incomes),
    )

    if not prev_expenses and not prev_incomes:
        logger.info("SKIP: Previous month has no data, returning False")
        return False

    # Passo 3: Replicar despesas
    replicated_count = 0
    for exp in prev_expenses:
        if exp.parcela_atual is not None and exp.parcela_total is not None:
            # Despesa parcelada
            if exp.parcela_atual < exp.parcela_total:
                logger.info(
                    "REPLICATE installment: '%s' parcela %d/%d -> %d/%d",
                    exp.nome, exp.parcela_atual, exp.parcela_total,
                    exp.parcela_atual + 1, exp.parcela_total,
                )
                new_exp = Expense(
                    user_id=user_id,  # CR-002
                    mes_referencia=target_mes,
                    nome=exp.nome,
                    valor=exp.valor,
                    vencimento=adjust_vencimento_to_month(
                        exp.vencimento, target_mes
                    ),
                    parcela_atual=exp.parcela_atual + 1,
                    parcela_total=exp.parcela_total,
                    recorrente=exp.recorrente,
                    status=ExpenseStatus.PENDENTE.value,
                )
                db.add(new_exp)
                replicated_count += 1
            else:
                logger.info(
                    "SKIP last installment: '%s' parcela %d/%d",
                    exp.nome, exp.parcela_atual, exp.parcela_total,
                )
        else:
            # Despesa sem parcela
            if exp.recorrente:
                logger.info("REPLICATE recurring: '%s'", exp.nome)
                new_exp = Expense(
                    user_id=user_id,  # CR-002
                    mes_referencia=target_mes,
                    nome=exp.nome,
                    valor=exp.valor,
                    vencimento=adjust_vencimento_to_month(
                        exp.vencimento, target_mes
                    ),
                    parcela_atual=None,
                    parcela_total=None,
                    recorrente=True,
                    status=ExpenseStatus.PENDENTE.value,
                )
                db.add(new_exp)
                replicated_count += 1
            else:
                logger.info(
                    "SKIP non-recurring: '%s' (recorrente=%s)",
                    exp.nome, exp.recorrente,
                )

    # Passo 4: Replicar receitas
    replicated_incomes = 0
    for inc in prev_incomes:
        if inc.recorrente:
            logger.info("REPLICATE income: '%s'", inc.nome)
            new_inc = Income(
                user_id=user_id,  # CR-002
                mes_referencia=target_mes,
                nome=inc.nome,
                valor=inc.valor,
                data=(
                    adjust_vencimento_to_month(inc.data, target_mes)
                    if inc.data
                    else None
                ),
                recorrente=True,
            )
            db.add(new_inc)
            replicated_incomes += 1
        else:
            logger.info("SKIP non-recurring income: '%s'", inc.nome)

    logger.info(
        "Replication complete: %d expenses, %d incomes replicated for %s",
        replicated_count, replicated_incomes, target_mes,
    )

    db.commit()
    return True


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

    return {
        "mes_referencia": mes_referencia,
        "total_despesas": round(total_despesas, 2),
        "total_receitas": round(total_receitas, 2),
        "saldo_livre": round(total_receitas - total_despesas, 2),
        "expenses": expenses,
        "incomes": incomes,
    }
