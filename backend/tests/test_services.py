"""Tests for RF-06: Month transition / expense replication."""
from datetime import date

from app.services import generate_month_data
from app import crud
from app.models import Expense, Income, ExpenseStatus, User


class TestGenerateMonthData:
    """Test generate_month_data() replication logic."""

    def test_replicates_recurring_expense(self, db, test_user, january_data):
        """Recurring expense (recorrente=True) should be replicated."""
        result = generate_month_data(db, date(2026, 2, 1), test_user.id)
        assert result is True

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        recurring = [e for e in feb_expenses if e.nome == "Aluguel"]
        assert len(recurring) == 1
        assert recurring[0].recorrente is True
        assert recurring[0].status == ExpenseStatus.PENDENTE.value
        assert recurring[0].parcela_atual is None
        assert recurring[0].parcela_total is None

    def test_replicates_installment_expense(self, db, test_user, january_data):
        """Installment expense should replicate with parcela_atual + 1."""
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        installment = [e for e in feb_expenses if e.nome == "TV Parcela"]
        assert len(installment) == 1
        assert installment[0].parcela_atual == 4  # was 3
        assert installment[0].parcela_total == 10
        assert installment[0].status == ExpenseStatus.PENDENTE.value

    def test_does_not_replicate_nonrecurring(self, db, test_user, january_data):
        """Non-recurring, non-installment expense should NOT be replicated."""
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        jantar = [e for e in feb_expenses if e.nome == "Jantar"]
        assert len(jantar) == 0

    def test_replicates_recurring_income(self, db, test_user, january_data):
        """Recurring income should be replicated."""
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        feb_incomes = crud.get_incomes_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_incomes) == 1
        assert feb_incomes[0].nome == "Salario"
        assert feb_incomes[0].recorrente is True

    def test_total_replicated_count(self, db, test_user, january_data):
        """January has 3 expenses (1 recurring, 1 installment, 1 avulsa) + 1 income.
        February should get 2 expenses + 1 income."""
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        feb_incomes = crud.get_incomes_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_expenses) == 2  # Aluguel + TV Parcela
        assert len(feb_incomes) == 1   # Salario

    def test_idempotency_no_double_replication(self, db, test_user, january_data):
        """Calling generate_month_data twice should not double the data."""
        generate_month_data(db, date(2026, 2, 1), test_user.id)
        result = generate_month_data(db, date(2026, 2, 1), test_user.id)
        assert result is False

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_expenses) == 2  # Still 2, not 4

    def test_empty_previous_month_returns_false(self, db, test_user):
        """No data in previous month -> returns False."""
        result = generate_month_data(db, date(2026, 6, 1), test_user.id)
        assert result is False

        june_expenses = crud.get_expenses_by_month(db, date(2026, 6, 1), test_user.id)
        assert len(june_expenses) == 0

    def test_last_installment_not_replicated(self, db, test_user):
        """Expense at parcela_atual == parcela_total should NOT replicate."""
        exp = Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Geladeira",
            valor=300.00,
            vencimento=date(2026, 1, 10),
            parcela_atual=10,
            parcela_total=10,
            recorrente=False,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(exp)
        db.commit()

        result = generate_month_data(db, date(2026, 2, 1), test_user.id)
        # Function runs (returns True) but nothing replicated
        assert result is True

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_expenses) == 0

    def test_vencimento_adjusted_to_target_month(self, db, test_user):
        """Vencimento day should be clamped when target month is shorter."""
        exp = Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Conta Luz",
            valor=150.00,
            vencimento=date(2026, 1, 31),
            recorrente=True,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(exp)
        db.commit()

        generate_month_data(db, date(2026, 2, 1), test_user.id)

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_expenses) == 1
        # Feb 2026 has 28 days, so day 31 clamps to 28
        assert feb_expenses[0].vencimento == date(2026, 2, 28)

    def test_user_isolation(self, db, test_user, january_data):
        """User A's data should not leak into User B's month generation."""
        user_b = User(
            id="user-test-002",
            nome="User B",
            email="b@example.com",
            password_hash="hashed",
            email_verified=True,
        )
        db.add(user_b)
        db.commit()

        # User B has no data in January
        result = generate_month_data(db, date(2026, 2, 1), user_b.id)
        assert result is False

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), user_b.id)
        assert len(feb_expenses) == 0

    def test_status_reset_to_pendente(self, db, test_user, january_data):
        """All replicated expenses should have status Pendente, even if original was Pago."""
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        for exp in feb_expenses:
            assert exp.status == ExpenseStatus.PENDENTE.value
