import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User, Expense, Income, ExpenseStatus


@pytest.fixture
def db():
    """In-memory SQLite session for fast tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        id="user-test-001",
        nome="Test User",
        email="test@example.com",
        password_hash="hashed",
        email_verified=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def january_data(db, test_user):
    """Create sample expenses and incomes in January 2026."""
    expenses = [
        Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Aluguel",
            valor=1500.00,
            vencimento=date(2026, 1, 10),
            recorrente=True,
            status=ExpenseStatus.PENDENTE.value,
        ),
        Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="TV Parcela",
            valor=200.00,
            vencimento=date(2026, 1, 15),
            parcela_atual=3,
            parcela_total=10,
            recorrente=False,
            status=ExpenseStatus.PAGO.value,
        ),
        Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Jantar",
            valor=80.00,
            vencimento=date(2026, 1, 20),
            recorrente=False,
            status=ExpenseStatus.PENDENTE.value,
        ),
    ]
    incomes = [
        Income(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Salario",
            valor=5000.00,
            data=date(2026, 1, 5),
            recorrente=True,
        ),
    ]
    for e in expenses:
        db.add(e)
    for i in incomes:
        db.add(i)
    db.commit()
    return expenses, incomes
