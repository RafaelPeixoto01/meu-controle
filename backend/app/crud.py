from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import date

from app.models import Expense, Income


# ========== Expenses ==========

def get_expenses_by_month(db: Session, mes_referencia: date) -> list[Expense]:
    """Retorna todas as despesas de um mes, ordenadas por vencimento."""
    stmt = (
        select(Expense)
        .where(Expense.mes_referencia == mes_referencia)
        .order_by(Expense.vencimento)
    )
    return list(db.scalars(stmt).all())


def get_expense_by_id(db: Session, expense_id: str) -> Expense | None:
    """Retorna uma despesa por ID ou None."""
    return db.get(Expense, expense_id)


def create_expense(db: Session, expense: Expense) -> Expense:
    """Persiste uma nova despesa."""
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


def count_expenses_by_month(db: Session, mes_referencia: date) -> int:
    """Conta despesas no mes (usado pelo check de idempotencia da transicao)."""
    stmt = select(Expense).where(Expense.mes_referencia == mes_referencia)
    return len(list(db.scalars(stmt).all()))


# ========== Incomes ==========

def get_incomes_by_month(db: Session, mes_referencia: date) -> list[Income]:
    """Retorna todas as receitas de um mes, ordenadas por data."""
    stmt = (
        select(Income)
        .where(Income.mes_referencia == mes_referencia)
        .order_by(Income.data)
    )
    return list(db.scalars(stmt).all())


def get_income_by_id(db: Session, income_id: str) -> Income | None:
    """Retorna uma receita por ID ou None."""
    return db.get(Income, income_id)


def create_income(db: Session, income: Income) -> Income:
    """Persiste uma nova receita."""
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
