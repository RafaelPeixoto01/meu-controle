from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date

from app.models import Expense, Income, User, RefreshToken  # CR-002: User, RefreshToken


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
