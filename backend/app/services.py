import calendar
from datetime import date

from sqlalchemy.orm import Session

from app import crud
from app.models import Expense, ExpenseStatus, Income


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


def generate_month_data(db: Session, target_mes: date) -> bool:
    """
    RF-06: Algoritmo de Transicao de Mes.

    Chamado quando o usuario navega para um mes.
    Olha os dados do mes anterior e gera entradas faltantes para target_mes
    seguindo as regras de replicacao.

    Usa check de duplicidade por nome para evitar replicar itens que ja existem
    no mes-alvo, mas ainda permite adicionar itens novos do mes anterior.

    Retorna True se dados foram gerados, False caso contrario.
    """
    # Buscar dados do mes anterior
    prev_mes = get_previous_month(target_mes)
    prev_expenses = crud.get_expenses_by_month(db, prev_mes)
    prev_incomes = crud.get_incomes_by_month(db, prev_mes)

    if not prev_expenses and not prev_incomes:
        return False

    # Buscar nomes ja existentes no mes-alvo para evitar duplicatas
    existing_expenses = crud.get_expenses_by_month(db, target_mes)
    existing_incomes = crud.get_incomes_by_month(db, target_mes)
    existing_expense_names = {e.nome for e in existing_expenses}
    existing_income_names = {i.nome for i in existing_incomes}

    generated = False

    # Replicar despesas
    for exp in prev_expenses:
        if exp.nome in existing_expense_names:
            continue  # Ja existe no mes-alvo, pular

        if exp.parcela_atual is not None and exp.parcela_total is not None:
            # Despesa parcelada
            if exp.parcela_atual < exp.parcela_total:
                new_exp = Expense(
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
                generated = True
            # else: ultima parcela, NAO replica
        else:
            # Despesa sem parcela
            if exp.recorrente:
                new_exp = Expense(
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
                generated = True
            # else: nao recorrente, NAO replica

    # Replicar receitas
    for inc in prev_incomes:
        if inc.nome in existing_income_names:
            continue  # Ja existe no mes-alvo, pular

        if inc.recorrente:
            new_inc = Income(
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
            generated = True
        # else: nao recorrente, NAO replica

    if generated:
        db.commit()
    return generated


def get_monthly_summary(db: Session, mes_referencia: date) -> dict:
    """
    Constroi a visao mensal completa.
    Passos:
    1. Tenta gerar dados do mes se vazio (RF-06)
    2. Busca despesas e receitas
    3. Aplica auto-deteccao de status (RF-05)
    4. Calcula totalizadores (RF-04)
    """
    # Passo 1: Auto-gerar se necessario
    generate_month_data(db, mes_referencia)

    # Passo 2: Buscar dados
    expenses = crud.get_expenses_by_month(db, mes_referencia)
    incomes = crud.get_incomes_by_month(db, mes_referencia)

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
