from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date

from app.models import Expense, Income, User, RefreshToken, DailyExpense  # CR-002: User, RefreshToken; CR-005: DailyExpense


# ========== Expenses ==========

def get_expenses_by_month(db: Session, mes_referencia: date, user_id: str) -> list[Expense]:
    """Retorna despesas de um usuario em um mes, ordenadas por vencimento. (CR-002: user_id)"""
    stmt = (
        select(Expense)
        .where(Expense.user_id == user_id, Expense.mes_referencia == mes_referencia)
        .order_by(Expense.vencimento)
    )
    return list(db.scalars(stmt).all())


def get_expense_by_id(db: Session, expense_id: str, user_id: str) -> Expense | None:
    """Retorna uma despesa por ID se pertence ao usuario, ou None. (CR-002: ownership check)"""
    stmt = (
        select(Expense)
        .where(Expense.id == expense_id, Expense.user_id == user_id)
    )
    return db.scalars(stmt).first()


def create_expense(db: Session, expense: Expense) -> Expense:
    """Persiste uma nova despesa. user_id ja deve estar setado na instancia."""
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def update_expense(db: Session, expense: Expense) -> Expense:
    """Persiste alteracoes em uma despesa existente."""
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense: Expense) -> None:
    """Remove uma despesa."""
    db.delete(expense)
    db.commit()


def delete_expense_related(db: Session, target_expense: Expense) -> None:
    """Remove uma despesa e TODAS as relacionadas (parcelas ou recorrentes com mesmo nome) (CR-009)."""
    conditions = [
        Expense.user_id == target_expense.user_id,
        Expense.nome == target_expense.nome,
    ]
    
    if target_expense.parcela_total is not None and target_expense.parcela_total > 1:
        conditions.append(Expense.parcela_total == target_expense.parcela_total)
    elif target_expense.recorrente:
        conditions.append(Expense.recorrente == True)
    else:
        conditions.append(Expense.id == target_expense.id)

    stmt = select(Expense).where(*conditions)
    expenses = db.scalars(stmt).all()
    for e in expenses:
        db.delete(e)
    db.commit()


def count_expenses_by_month(db: Session, mes_referencia: date, user_id: str) -> int:
    """Conta despesas do usuario no mes (check de idempotencia da transicao). (CR-002: user_id)"""
    stmt = (
        select(Expense)
        .where(Expense.user_id == user_id, Expense.mes_referencia == mes_referencia)
    )
    return len(list(db.scalars(stmt).all()))


def expense_replica_exists(
    db: Session, target_mes: date, user_id: str, origem_id: str
) -> bool:
    """Checa se ja existe uma replica desta despesa no mes-alvo."""
    stmt = (
        select(Expense)
        .where(
            Expense.user_id == user_id,
            Expense.mes_referencia == target_mes,
            Expense.origem_id == origem_id,
        )
    )
    return db.scalars(stmt).first() is not None


# ========== Incomes ==========

def get_incomes_by_month(db: Session, mes_referencia: date, user_id: str) -> list[Income]:
    """Retorna receitas de um usuario em um mes, ordenadas por data. (CR-002: user_id)"""
    stmt = (
        select(Income)
        .where(Income.user_id == user_id, Income.mes_referencia == mes_referencia)
        .order_by(Income.data)
    )
    return list(db.scalars(stmt).all())


def get_income_by_id(db: Session, income_id: str, user_id: str) -> Income | None:
    """Retorna uma receita por ID se pertence ao usuario, ou None. (CR-002: ownership check)"""
    stmt = (
        select(Income)
        .where(Income.id == income_id, Income.user_id == user_id)
    )
    return db.scalars(stmt).first()


def create_income(db: Session, income: Income) -> Income:
    """Persiste uma nova receita. user_id ja deve estar setado na instancia."""
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def update_income(db: Session, income: Income) -> Income:
    """Persiste alteracoes em uma receita existente."""
    db.commit()
    db.refresh(income)
    return income


def delete_income(db: Session, income: Income) -> None:
    """Remove uma receita."""
    db.delete(income)
    db.commit()


def income_replica_exists(
    db: Session, target_mes: date, user_id: str, origem_id: str
) -> bool:
    """Checa se ja existe uma replica desta receita no mes-alvo."""
    stmt = (
        select(Income)
        .where(
            Income.user_id == user_id,
            Income.mes_referencia == target_mes,
            Income.origem_id == origem_id,
        )
    )
    return db.scalars(stmt).first() is not None


# ========== Daily Expenses (CR-005) ==========

def get_daily_expenses_by_month(db: Session, mes_referencia: date, user_id: str) -> list[DailyExpense]:
    """Retorna gastos diarios de um usuario em um mes, ordenados por data desc."""
    stmt = (
        select(DailyExpense)
        .where(DailyExpense.user_id == user_id, DailyExpense.mes_referencia == mes_referencia)
        .order_by(DailyExpense.data.desc(), DailyExpense.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_daily_expense_by_id(db: Session, daily_expense_id: str, user_id: str) -> DailyExpense | None:
    """Retorna um gasto diario por ID se pertence ao usuario."""
    stmt = (
        select(DailyExpense)
        .where(DailyExpense.id == daily_expense_id, DailyExpense.user_id == user_id)
    )
    return db.scalars(stmt).first()


def create_daily_expense(db: Session, daily_expense: DailyExpense) -> DailyExpense:
    """Persiste um novo gasto diario."""
    db.add(daily_expense)
    db.commit()
    db.refresh(daily_expense)
    return daily_expense


def update_daily_expense(db: Session, daily_expense: DailyExpense) -> DailyExpense:
    """Persiste alteracoes em um gasto diario existente."""
    db.commit()
    db.refresh(daily_expense)
    return daily_expense


def delete_daily_expense(db: Session, daily_expense: DailyExpense) -> None:
    """Remove um gasto diario."""
    db.delete(daily_expense)
    db.commit()


# ========== Users (CR-002) ==========

def get_user_by_email(db: Session, email: str) -> User | None:
    """Retorna usuario por email ou None."""
    stmt = select(User).where(User.email == email)
    return db.scalars(stmt).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Retorna usuario por ID ou None."""
    return db.get(User, user_id)


def get_user_by_google_id(db: Session, google_id: str) -> User | None:
    """Retorna usuario por Google ID ou None."""
    stmt = select(User).where(User.google_id == google_id)
    return db.scalars(stmt).first()


def create_user(db: Session, user: User) -> User:
    """Persiste um novo usuario."""
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User) -> User:
    """Persiste alteracoes em um usuario existente."""
    db.commit()
    db.refresh(user)
    return user


# ========== Refresh Tokens (CR-002) ==========

def create_refresh_token(db: Session, token: RefreshToken) -> RefreshToken:
    """Persiste um novo refresh token."""
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_refresh_token_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
    """Retorna refresh token pelo hash ou None."""
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    return db.scalars(stmt).first()


def delete_refresh_token(db: Session, token: RefreshToken) -> None:
    """Remove um refresh token (rotacao)."""
    db.delete(token)
    db.commit()


def delete_user_refresh_tokens(db: Session, user_id: str) -> None:
    """Remove todos os refresh tokens de um usuario (logout total)."""
    stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
    tokens = list(db.scalars(stmt).all())
    for token in tokens:
        db.delete(token)
    db.commit()


# ========== Installments (CR-007) ==========

def get_installment_expenses_grouped(db: Session, user_id: str) -> dict:
    """
    Busca todas as despesas parceladas do usuario e agrupa por nome/total de parcelas.
    Retorna dicionario com estrutura pronta para o schema InstallmentsResponse.
    """
    # 1. Buscar todas as despesas parceladas (parcela_total > 1)
    stmt = (
        select(Expense)
        .where(
            Expense.user_id == user_id,
            Expense.parcela_total > 1
        )
        .order_by(Expense.vencimento)
    )
    expenses = list(db.scalars(stmt).all())

    # 2. Agrupar em memoria
    # Chave do grupo: (nome_normalizado, parcela_total) para diferenciar
    # "Compra X (10x)" de "Compra X (5x)" se tiverem mesmo nome
    groups_map = {}
    
    # Totais globais
    global_gasto = 0.0
    global_pago = 0.0
    global_pendente = 0.0
    global_atrasado = 0.0

    from app.models import ExpenseStatus

    for exp in expenses:
        # Normalizar chave
        key = (exp.nome.strip().lower(), exp.parcela_total)
        
        if key not in groups_map:
            groups_map[key] = {
                "nome": exp.nome,  # Mantem casing original do primeiro
                "parcela_total": exp.parcela_total,
                "installments": [],
                "valor_total_compra": 0.0,
                "valor_pago": 0.0,
                "valor_restante": 0.0,
                "tem_pendencia": False
            }
        
        group = groups_map[key]
        group["installments"].append(exp)
        
        # Somar valores
        val = float(exp.valor)
        group["valor_total_compra"] += val
        
        if exp.status == ExpenseStatus.PAGO.value:
            group["valor_pago"] += val
        else:
            group["valor_restante"] += val
            group["tem_pendencia"] = True
            
        # Totais globais
        global_gasto += val
        if exp.status == ExpenseStatus.PAGO.value:
            global_pago += val
        elif exp.status == ExpenseStatus.PENDENTE.value:
            global_pendente += val
        elif exp.status == ExpenseStatus.ATRASADO.value:
            global_atrasado += val
            # Atrasado tambem conta como pendente no 'restante' do grupo, mas separadamente no global

    # 3. Formatar lista de grupos
    final_groups = []
    
    # Ordenar grupos pelo input mais recente (vencimento da ultima parcela ou similar)
    # Por simplicidade, vamos ordenar por nome
    sorted_keys = sorted(groups_map.keys(), key=lambda k: k[0])
    
    for key in sorted_keys:
        g = groups_map[key]
        
        # Determinar status geral do grupo
        if g["valor_restante"] == 0 and not g["tem_pendencia"]:
            status_geral = "Concluído"
        else:
            status_geral = "Em andamento"
            
        final_groups.append({
            "nome": g["nome"],
            "parcela_total": g["parcela_total"],
            "status_geral": status_geral,
            "valor_total_compra": round(g["valor_total_compra"], 2),
            "valor_pago": round(g["valor_pago"], 2),
            "valor_restante": round(g["valor_restante"], 2),
            "installments": g["installments"]
        })

    return {
        "groups": final_groups,
        "total_gasto": round(global_gasto, 2),
        "total_pago": round(global_pago, 2),
        "total_pendente": round(global_pendente, 2),
        "total_atrasado": round(global_atrasado, 2)
    }

