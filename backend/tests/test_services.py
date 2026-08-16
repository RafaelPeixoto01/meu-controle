"""Tests for RF-06: Month transition / expense replication."""
from datetime import date

from app.services import create_expense_with_installments, generate_month_data
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
        assert result is False  # Nothing to replicate

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

    def test_origem_id_set_on_replicas(self, db, test_user, january_data):
        """Replicated expenses should have origem_id pointing to source expense."""
        jan_expenses = crud.get_expenses_by_month(db, date(2026, 1, 1), test_user.id)
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        for feb_exp in feb_expenses:
            assert feb_exp.origem_id is not None
            # origem_id should match a January expense
            source_ids = {e.id for e in jan_expenses}
            assert feb_exp.origem_id in source_ids

    def test_incremental_replication_new_expense(self, db, test_user):
        """BUG FIX: Creating expense after first navigation should still replicate."""
        # 1. Create first expense in January
        exp_a = Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Aluguel",
            valor=1500.00,
            vencimento=date(2026, 1, 10),
            recorrente=True,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(exp_a)
        db.commit()

        # 2. Navigate to February → replicates Aluguel
        result1 = generate_month_data(db, date(2026, 2, 1), test_user.id)
        assert result1 is True
        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_expenses) == 1

        # 3. Add second expense to January
        exp_b = Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Internet",
            valor=100.00,
            vencimento=date(2026, 1, 15),
            recorrente=True,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(exp_b)
        db.commit()

        # 4. Navigate to February again → should replicate Internet
        result2 = generate_month_data(db, date(2026, 2, 1), test_user.id)
        assert result2 is True
        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_expenses) == 2  # Aluguel + Internet
        names = {e.nome for e in feb_expenses}
        assert names == {"Aluguel", "Internet"}

    def test_incremental_replication_no_duplicates(self, db, test_user):
        """Incremental replication should not duplicate already-replicated expenses."""
        exp = Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Aluguel",
            valor=1500.00,
            vencimento=date(2026, 1, 10),
            recorrente=True,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(exp)
        db.commit()

        # Call 3 times — should always result in exactly 1 replica
        generate_month_data(db, date(2026, 2, 1), test_user.id)
        generate_month_data(db, date(2026, 2, 1), test_user.id)
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_expenses) == 1

    def test_incremental_replication_installment(self, db, test_user):
        """Adding installment expense after first navigation should replicate it."""
        # 1. Create recurring expense in January
        exp_a = Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Aluguel",
            valor=1500.00,
            vencimento=date(2026, 1, 10),
            recorrente=True,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(exp_a)
        db.commit()

        # 2. Navigate to February
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        # 3. Add installment expense to January
        exp_b = Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="TV",
            valor=200.00,
            vencimento=date(2026, 1, 20),
            parcela_atual=1,
            parcela_total=12,
            recorrente=False,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(exp_b)
        db.commit()

        # 4. Navigate to February again
        result = generate_month_data(db, date(2026, 2, 1), test_user.id)
        assert result is True

        feb_expenses = crud.get_expenses_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_expenses) == 2

        tv = [e for e in feb_expenses if e.nome == "TV"]
        assert len(tv) == 1
        assert tv[0].parcela_atual == 2
        assert tv[0].parcela_total == 12

    def test_incremental_replication_income(self, db, test_user):
        """Adding recurring income after first navigation should replicate it."""
        # 1. Create expense in January
        exp = Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Aluguel",
            valor=1500.00,
            vencimento=date(2026, 1, 10),
            recorrente=True,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(exp)
        db.commit()

        # 2. Navigate to February
        generate_month_data(db, date(2026, 2, 1), test_user.id)

        # 3. Add income to January
        inc = Income(
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Salario",
            valor=5000.00,
            data=date(2026, 1, 5),
            recorrente=True,
        )
        db.add(inc)
        db.commit()

        # 4. Navigate to February again
        result = generate_month_data(db, date(2026, 2, 1), test_user.id)
        assert result is True

        feb_incomes = crud.get_incomes_by_month(db, date(2026, 2, 1), test_user.id)
        assert len(feb_incomes) == 1
        assert feb_incomes[0].nome == "Salario"


class TestCreateExpenseWithInstallments:
    """CR-049: criacao upfront de parcelas, extraida do router de expenses."""

    def test_cria_apenas_uma_despesa_quando_nao_parcelada(self, db, test_user):
        expense, criadas = create_expense_with_installments(
            db,
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Netflix",
            valor=39.90,
            vencimento=date(2026, 3, 10),
        )
        db.commit()

        assert criadas == 1
        assert expense.recorrente is True
        assert expense.status == ExpenseStatus.PENDENTE.value
        todas = db.query(Expense).filter(Expense.user_id == test_user.id).all()
        assert len(todas) == 1

    def test_cria_parcelas_futuras_upfront(self, db, test_user):
        """Parcela 3/10 gera a atual + 7 futuras, avancando mes e vencimento."""
        expense, criadas = create_expense_with_installments(
            db,
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Notebook",
            valor=250.00,
            vencimento=date(2026, 3, 15),
            categoria="Compras Pessoais",
            subcategoria="Eletrônicos",
            parcela_atual=3,
            parcela_total=10,
            recorrente=False,
        )
        db.commit()

        assert criadas == 8  # 3..10
        todas = db.query(Expense).order_by(Expense.parcela_atual).all()
        assert [e.parcela_atual for e in todas] == [3, 4, 5, 6, 7, 8, 9, 10]
        assert todas[0].id == expense.id
        # A ultima parcela (10) cai 7 meses depois de marco/2026
        assert todas[-1].mes_referencia == date(2026, 10, 1)
        assert todas[-1].vencimento == date(2026, 10, 15)
        # Futuras herdam categoria e nascem Pendente + recorrente=False
        assert all(e.categoria == "Compras Pessoais" for e in todas)
        assert all(e.status == ExpenseStatus.PENDENTE.value for e in todas[1:])
        assert all(e.recorrente is False for e in todas[1:])

    def test_status_primeira_parcela_configuravel(self, db, test_user):
        """RN-044: importacao marca a parcela ja cobrada na fatura como Paga."""
        expense, criadas = create_expense_with_installments(
            db,
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Netshoes",
            valor=149.90,
            vencimento=date(2026, 3, 20),
            parcela_atual=1,
            parcela_total=3,
            recorrente=False,
            status_primeira=ExpenseStatus.PAGO.value,
        )
        db.commit()

        assert criadas == 3
        assert expense.status == ExpenseStatus.PAGO.value
        futuras = db.query(Expense).filter(Expense.parcela_atual > 1).all()
        assert all(e.status == ExpenseStatus.PENDENTE.value for e in futuras)

    def test_vencimento_ajusta_mes_curto(self, db, test_user):
        """add_months preserva o dia mas respeita meses curtos (31/01 -> 28/02)."""
        create_expense_with_installments(
            db,
            user_id=test_user.id,
            mes_referencia=date(2026, 1, 1),
            nome="Compra",
            valor=100.00,
            vencimento=date(2026, 1, 31),
            parcela_atual=1,
            parcela_total=2,
            recorrente=False,
        )
        db.commit()

        segunda = db.query(Expense).filter(Expense.parcela_atual == 2).one()
        assert segunda.vencimento == date(2026, 2, 28)

    def test_skip_existing_nao_recria_parcela_ja_gravada(self, db, test_user):
        """RN-046: reimportar a fatura seguinte nao duplica parcelas ja criadas."""
        db.add(
            Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 4, 1),
                nome="Notebook",
                valor=250.00,
                vencimento=date(2026, 4, 15),
                parcela_atual=2,
                parcela_total=3,
                recorrente=False,
                status=ExpenseStatus.PENDENTE.value,
            )
        )
        db.commit()

        _, criadas = create_expense_with_installments(
            db,
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Notebook",
            valor=250.00,
            vencimento=date(2026, 3, 15),
            parcela_atual=1,
            parcela_total=3,
            recorrente=False,
            skip_existing=True,
        )
        db.commit()

        assert criadas == 2  # parcela 1 + parcela 3 (a 2 ja existia)
        parcelas_2 = db.query(Expense).filter(Expense.parcela_atual == 2).all()
        assert len(parcelas_2) == 1
