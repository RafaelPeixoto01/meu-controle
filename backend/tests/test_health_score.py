"""
CR-026: Testes do servico de calculo do Score de Saude Financeira.
Cenarios da secao 14 do CR-026.
"""
import pytest
from datetime import date, datetime
from unittest.mock import patch

from app.models import Expense, Income, DailyExpense, ExpenseStatus
from app.health_score import calculate_health_score, calculate_conservative_score, generate_actions


# ========== Fixtures ==========

@pytest.fixture
def scenario_1_healthy(db, test_user):
    """
    Cenario 1: Situacao saudavel
    - Renda: R$ 10.000
    - Fixos: R$ 4.500 (45%)
    - Parcelas: 2 ativas (R$ 800 total, 8%), nenhuma pendente
    - Variaveis: R$ 2.000 (20%)
    - Saldo livre: 35%
    - Tudo pago em dia, 22 dias de registro, comprometimento reduziu vs. mes anterior
    - Esperado: D1=25, D2~18, D3=25, D4~23 → Score ~91 (Excelente)
    """
    mes = date(2026, 3, 1)

    # Receitas
    income = Income(user_id=test_user.id, mes_referencia=mes, nome="Salario", valor=10000.00,
                    data=date(2026, 3, 5), recorrente=True)
    db.add(income)

    # Despesas fixas: R$ 4.500
    fixos = [
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Aluguel", valor=2000.00,
                vencimento=date(2026, 3, 10), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Condominio", valor=800.00,
                vencimento=date(2026, 3, 10), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Energia", valor=300.00,
                vencimento=date(2026, 3, 15), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Internet", valor=150.00,
                vencimento=date(2026, 3, 20), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Plano Saude", valor=450.00,
                vencimento=date(2026, 3, 15), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Seguro Auto", valor=200.00,
                vencimento=date(2026, 3, 20), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Streaming", valor=100.00,
                vencimento=date(2026, 3, 10), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Academia", valor=100.00,
                vencimento=date(2026, 3, 5), recorrente=True, status=ExpenseStatus.PAGO.value),
    ]
    # Parcelas: Celular 12x R$ 200 (2 ativas), Notebook 10x R$ 600 (2 ativas) → total 800/mes
    parcela_celular = Expense(user_id=test_user.id, mes_referencia=mes, nome="Celular", valor=200.00,
                              vencimento=date(2026, 3, 15), parcela_atual=5, parcela_total=12,
                              recorrente=False, status=ExpenseStatus.PAGO.value)
    parcela_notebook = Expense(user_id=test_user.id, mes_referencia=mes, nome="Notebook", valor=200.00,
                               vencimento=date(2026, 3, 15), parcela_atual=3, parcela_total=10,
                               recorrente=False, status=ExpenseStatus.PAGO.value)

    for e in fixos + [parcela_celular, parcela_notebook]:
        db.add(e)

    # Daily expenses: R$ 2.000 em 22 dias
    daily = []
    for day in range(1, 23):
        daily.append(DailyExpense(
            user_id=test_user.id, mes_referencia=mes,
            descricao=f"Gasto dia {day}", valor=round(2000.0 / 22, 2),
            data=date(2026, 3, day), categoria="Alimentação", subcategoria="Restaurante",
            metodo_pagamento="Pix",
        ))
    for de in daily:
        db.add(de)

    db.commit()

    all_expenses = fixos + [parcela_celular, parcela_notebook]

    # Build installment groups (simulate crud output)
    installment_groups = [
        {
            "nome": "Celular",
            "parcela_total": 12,
            "status_geral": "Em andamento",
            "valor_total_compra": 2400.00,
            "valor_pago": 1000.00,
            "valor_restante": 1400.00,
            "installments": [parcela_celular],
        },
        {
            "nome": "Notebook",
            "parcela_total": 10,
            "status_geral": "Em andamento",
            "valor_total_compra": 2000.00,
            "valor_pago": 600.00,
            "valor_restante": 1400.00,
            "installments": [parcela_notebook],
        },
    ]

    return {
        "renda": 10000.00,
        "expenses": all_expenses,
        "daily_expenses": daily,
        "installment_groups": installment_groups,
        "daily_expense_history": [(date(2026, 1, 1), 2100.0), (date(2026, 2, 1), 1900.0), (date(2026, 3, 1), 2000.0)],
        "prev_month_comprometimento": 70.0,  # reduziu para ~65%
        "mes_atual": mes,
    }


@pytest.fixture
def scenario_3_first_month(db, test_user):
    """
    Cenario 3: Primeiro mes, poucos dados
    - Renda: R$ 8.000
    - Fixos: R$ 3.000 (37,5%)
    - Parcelas: nenhuma
    - Variaveis: R$ 500 em 5 dias (projecao ~R$ 3.000)
    - Saldo livre: ~25%
    - 5 dias de registro, sem historico anterior
    - Esperado: D1=25, D2=25, D3=25, D4~14 → Score ~89 (Excelente)
    """
    mes = date(2026, 3, 1)

    income = Income(user_id=test_user.id, mes_referencia=mes, nome="Salario", valor=8000.00,
                    data=date(2026, 3, 5), recorrente=True)
    db.add(income)

    fixos = [
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Aluguel", valor=1500.00,
                vencimento=date(2026, 3, 10), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Condominio", valor=500.00,
                vencimento=date(2026, 3, 10), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Energia", valor=250.00,
                vencimento=date(2026, 3, 15), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Internet", valor=150.00,
                vencimento=date(2026, 3, 20), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Plano Saude", valor=400.00,
                vencimento=date(2026, 3, 15), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Seguro", valor=200.00,
                vencimento=date(2026, 3, 20), recorrente=True, status=ExpenseStatus.PAGO.value),
    ]
    for e in fixos:
        db.add(e)

    daily = []
    for day in range(1, 6):
        daily.append(DailyExpense(
            user_id=test_user.id, mes_referencia=mes,
            descricao=f"Gasto dia {day}", valor=100.00,
            data=date(2026, 3, day), categoria="Alimentação", subcategoria="Restaurante",
            metodo_pagamento="Pix",
        ))
    for de in daily:
        db.add(de)

    db.commit()

    return {
        "renda": 8000.00,
        "expenses": fixos,
        "daily_expenses": daily,
        "installment_groups": [],
        "daily_expense_history": [],  # primeiro mes
        "prev_month_comprometimento": None,  # primeiro mes
        "mes_atual": mes,
    }


@pytest.fixture
def scenario_4_critical(db, test_user):
    """
    Cenario 4: Situacao critica
    - Renda: R$ 5.000
    - Fixos: R$ 4.500 (90%)
    - Parcelas: 12 ativas (60% da renda), 3 pendentes
    - Variaveis: R$ 1.500
    - Saldo livre: negativo
    - 3 despesas atrasadas, 2 dias de registro, comprometimento aumentou
    - Esperado: D1=0, D2=0, D3=0, D4~3 → Score ~3 (Critica)
    """
    mes = date(2026, 3, 1)

    income = Income(user_id=test_user.id, mes_referencia=mes, nome="Salario", valor=5000.00,
                    data=date(2026, 3, 5), recorrente=True)
    db.add(income)

    # Fixos: R$ 4.500
    fixos = [
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Aluguel", valor=2000.00,
                vencimento=date(2026, 3, 10), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Condominio", valor=800.00,
                vencimento=date(2026, 3, 10), recorrente=True, status=ExpenseStatus.PAGO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Energia", valor=400.00,
                vencimento=date(2026, 3, 5), recorrente=True, status=ExpenseStatus.ATRASADO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Internet", valor=200.00,
                vencimento=date(2026, 3, 5), recorrente=True, status=ExpenseStatus.ATRASADO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Plano Saude", valor=600.00,
                vencimento=date(2026, 3, 5), recorrente=True, status=ExpenseStatus.ATRASADO.value),
        Expense(user_id=test_user.id, mes_referencia=mes, nome="Diversos", valor=500.00,
                vencimento=date(2026, 3, 20), recorrente=True, status=ExpenseStatus.PENDENTE.value),
    ]
    for e in fixos:
        db.add(e)

    # 12 parcelas ativas + 3 pendentes (0 de Y) = 15 groups
    installment_groups = []
    parcela_expenses = []
    for i in range(1, 13):
        exp = Expense(user_id=test_user.id, mes_referencia=mes, nome=f"Parcela {i}",
                      valor=250.00, vencimento=date(2026, 3, 15), parcela_atual=2,
                      parcela_total=10, recorrente=False, status=ExpenseStatus.PAGO.value)
        db.add(exp)
        parcela_expenses.append(exp)
        installment_groups.append({
            "nome": f"Parcela {i}",
            "parcela_total": 10,
            "status_geral": "Em andamento",
            "valor_total_compra": 2500.00,
            "valor_pago": 500.00,
            "valor_restante": 2000.00,
            "installments": [exp],
        })

    # 3 pendentes (0 pagas)
    for i in range(1, 4):
        exp = Expense(user_id=test_user.id, mes_referencia=mes, nome=f"Pendente {i}",
                      valor=300.00, vencimento=date(2026, 4, 15), parcela_atual=1,
                      parcela_total=6, recorrente=False, status=ExpenseStatus.PENDENTE.value)
        db.add(exp)
        installment_groups.append({
            "nome": f"Pendente {i}",
            "parcela_total": 6,
            "status_geral": "Em andamento",
            "valor_total_compra": 1800.00,
            "valor_pago": 0.00,
            "valor_restante": 1800.00,
            "installments": [exp],
        })

    # Daily: R$ 1.500 em 2 dias
    daily = [
        DailyExpense(user_id=test_user.id, mes_referencia=mes, descricao="Compras", valor=1000.00,
                     data=date(2026, 3, 1), categoria="Alimentação", subcategoria="Supermercado",
                     metodo_pagamento="Cartão de Crédito"),
        DailyExpense(user_id=test_user.id, mes_referencia=mes, descricao="Farmacia", valor=500.00,
                     data=date(2026, 3, 2), categoria="Saúde", subcategoria="Farmácia",
                     metodo_pagamento="Pix"),
    ]
    for de in daily:
        db.add(de)

    db.commit()

    all_expenses = fixos + parcela_expenses

    return {
        "renda": 5000.00,
        "expenses": all_expenses,
        "daily_expenses": daily,
        "installment_groups": installment_groups,
        "daily_expense_history": [(date(2026, 1, 1), 1200.0), (date(2026, 2, 1), 1300.0), (date(2026, 3, 1), 1500.0)],
        "prev_month_comprometimento": 80.0,  # aumentou
        "mes_atual": mes,
    }


# ========== Tests ==========

class TestHealthScoreCalculation:
    """Testes do calculo das 4 dimensoes do score."""

    def test_scenario_1_healthy(self, db, test_user, scenario_1_healthy):
        """Cenario 1: Situacao saudavel → Score ~91 (Excelente)."""
        s = scenario_1_healthy
        result = calculate_health_score(
            renda=s["renda"], expenses=s["expenses"], daily_expenses=s["daily_expenses"],
            installment_groups=s["installment_groups"],
            daily_expense_history=s["daily_expense_history"],
            prev_month_comprometimento=s["prev_month_comprometimento"],
            mes_atual=s["mes_atual"],
        )

        score = result["score"]
        dims = result["dimensoes"]

        # D1: 45% comprometimento → 25 pontos
        assert dims["d1_comprometimento"]["pontos"] == 25
        # D2: 2 parcelas, ~4% da renda → alto
        assert dims["d2_parcelas"]["pontos"] >= 10
        # D3: saldo livre ~35% → 25 pontos
        assert dims["d3_poupanca"]["pontos"] == 25
        # D4: tudo pago em dia + 22 dias registro → alto
        assert dims["d4_comportamento"]["pontos"] >= 18

        # Total: Excelente
        assert score["total"] >= 80
        assert score["classificacao"] in ("Excelente", "Saudável")

    def test_scenario_3_first_month(self, db, test_user, scenario_3_first_month):
        """Cenario 3: Primeiro mes, poucos dados → Score ~89 (Excelente)."""
        s = scenario_3_first_month
        result = calculate_health_score(
            renda=s["renda"], expenses=s["expenses"], daily_expenses=s["daily_expenses"],
            installment_groups=s["installment_groups"],
            daily_expense_history=s["daily_expense_history"],
            prev_month_comprometimento=s["prev_month_comprometimento"],
            mes_atual=s["mes_atual"],
        )

        score = result["score"]
        dims = result["dimensoes"]

        # D1: 37.5% → 25
        assert dims["d1_comprometimento"]["pontos"] == 25
        # D2: sem parcelas → 15 (10 + 5 + 0 + 0)
        assert dims["d2_parcelas"]["pontos"] == 15
        # D3: saldo livre ~25% (3000 fixos + ~3000 projetados = 6000, livre = 2000 = 25%) → 25
        assert dims["d3_poupanca"]["pontos"] >= 20
        # D4c: primeiro mes → 3 (neutro)
        assert dims["d4_comportamento"]["subfatores"]["d4c_tendencia"]["primeiro_mes"] is True
        assert dims["d4_comportamento"]["subfatores"]["d4c_tendencia"]["pontos"] == 3

        # Total: alto
        assert score["total"] >= 70

    def test_scenario_4_critical(self, db, test_user, scenario_4_critical):
        """Cenario 4: Situacao critica → Score baixo (Critica/Atencao)."""
        s = scenario_4_critical
        result = calculate_health_score(
            renda=s["renda"], expenses=s["expenses"], daily_expenses=s["daily_expenses"],
            installment_groups=s["installment_groups"],
            daily_expense_history=s["daily_expense_history"],
            prev_month_comprometimento=s["prev_month_comprometimento"],
            mes_atual=s["mes_atual"],
        )

        score = result["score"]
        dims = result["dimensoes"]

        # D1: 90% comprometimento → 0
        assert dims["d1_comprometimento"]["pontos"] == 0
        # D2: muitas parcelas + pendentes → baixo
        assert dims["d2_parcelas"]["pontos"] <= 5
        # D3: saldo negativo → 0
        assert dims["d3_poupanca"]["pontos"] == 0
        # D4: some late payments + low registration + increased commitment
        assert dims["d4_comportamento"]["pontos"] <= 15

        # Total: Critica or Atencao
        assert score["total"] <= 25
        assert score["classificacao"] == "Crítica"

    def test_scenario_5_no_income(self, db, test_user):
        """Cenario 5: Sem receitas → Score 0, mensagem especial."""
        result = calculate_health_score(
            renda=0, expenses=[], daily_expenses=[],
            installment_groups=[], daily_expense_history=[],
            prev_month_comprometimento=None, mes_atual=date(2026, 3, 1),
        )

        assert result["score"]["total"] == 0
        assert "Cadastre sua renda" in result["score"]["mensagem"]

    def test_scenario_6_no_expenses(self, db, test_user):
        """Cenario 6: Sem despesas → Score 100."""
        result = calculate_health_score(
            renda=10000.00, expenses=[], daily_expenses=[],
            installment_groups=[], daily_expense_history=[],
            prev_month_comprometimento=None, mes_atual=date(2026, 3, 1),
        )

        assert result["score"]["total"] == 100
        assert result["score"]["classificacao"] == "Excelente"
        assert result["dimensoes"]["d1_comprometimento"]["pontos"] == 25
        assert result["dimensoes"]["d2_parcelas"]["pontos"] == 25
        assert result["dimensoes"]["d3_poupanca"]["pontos"] == 25
        assert result["dimensoes"]["d4_comportamento"]["pontos"] == 25

    def test_d1_faixas(self, db, test_user):
        """Testa faixas de D1 com diferentes niveis de comprometimento."""
        from app.health_score import _calc_d1

        assert _calc_d1(10000, 4500)["pontos"] == 25   # 45%
        assert _calc_d1(10000, 5500)["pontos"] == 20   # 55%
        assert _calc_d1(10000, 6500)["pontos"] == 12   # 65%
        assert _calc_d1(10000, 7500)["pontos"] == 5    # 75%
        assert _calc_d1(10000, 8500)["pontos"] == 0    # 85%

    def test_d3_faixas(self, db, test_user):
        """Testa faixas de D3 com diferentes percentuais de saldo livre."""
        from app.health_score import _calc_d3

        # >= 20% → 25
        assert _calc_d3(10000, 5000, 2000, 30, 31)["pontos"] == 25   # 30% livre
        # 15-19.9% → 20
        assert _calc_d3(10000, 6000, 2200, 30, 31)["pontos"] == 20   # 18% livre
        # 10-14.9% → 15
        assert _calc_d3(10000, 7000, 1800, 30, 31)["pontos"] == 15   # 12% livre
        # 5-9.9% → 8
        assert _calc_d3(10000, 7500, 1800, 30, 31)["pontos"] == 8    # 7% livre
        # 0.1-4.9% → 3
        assert _calc_d3(10000, 8000, 1800, 30, 31)["pontos"] == 3    # 2% livre
        # <= 0% → 0
        assert _calc_d3(10000, 8000, 3000, 30, 31)["pontos"] == 0    # -10% livre

    def test_classification_faixas(self):
        """Testa classificacao correta para cada faixa de score."""
        from app.health_score import classify_score

        assert classify_score(10)[0] == "Crítica"
        assert classify_score(25)[0] == "Crítica"
        assert classify_score(30)[0] == "Atenção"
        assert classify_score(45)[0] == "Atenção"
        assert classify_score(50)[0] == "Estável"
        assert classify_score(65)[0] == "Estável"
        assert classify_score(70)[0] == "Saudável"
        assert classify_score(85)[0] == "Saudável"
        assert classify_score(90)[0] == "Excelente"
        assert classify_score(100)[0] == "Excelente"


class TestConservativeScenario:
    """Testes do cenario conservador."""

    def test_no_pending_returns_none(self, db, test_user, scenario_1_healthy):
        """Sem parcelas pendentes → retorna None."""
        s = scenario_1_healthy
        result = calculate_health_score(
            renda=s["renda"], expenses=s["expenses"], daily_expenses=s["daily_expenses"],
            installment_groups=s["installment_groups"],
            daily_expense_history=s["daily_expense_history"],
            prev_month_comprometimento=s["prev_month_comprometimento"],
            mes_atual=s["mes_atual"],
        )
        conservative = calculate_conservative_score(result, s["installment_groups"], s["renda"])
        assert conservative is None

    def test_with_pending_returns_lower_score(self, db, test_user, scenario_4_critical):
        """Com parcelas pendentes → score conservador menor ou igual."""
        s = scenario_4_critical
        result = calculate_health_score(
            renda=s["renda"], expenses=s["expenses"], daily_expenses=s["daily_expenses"],
            installment_groups=s["installment_groups"],
            daily_expense_history=s["daily_expense_history"],
            prev_month_comprometimento=s["prev_month_comprometimento"],
            mes_atual=s["mes_atual"],
        )
        conservative = calculate_conservative_score(result, s["installment_groups"], s["renda"])
        assert conservative is not None
        assert conservative["score"] <= result["score"]["total"]
        assert len(conservative["parcelas_pendentes"]) == 3


class TestActionsGenerator:
    """Testes do gerador de acoes sugeridas."""

    def test_generates_actions_for_low_dimensions(self, db, test_user, scenario_4_critical):
        """Gera acoes para dimensoes com pontuacao baixa."""
        s = scenario_4_critical
        result = calculate_health_score(
            renda=s["renda"], expenses=s["expenses"], daily_expenses=s["daily_expenses"],
            installment_groups=s["installment_groups"],
            daily_expense_history=s["daily_expense_history"],
            prev_month_comprometimento=s["prev_month_comprometimento"],
            mes_atual=s["mes_atual"],
        )
        actions = generate_actions(result, s["renda"], s["expenses"], s["daily_expenses"],
                                   s["installment_groups"])
        assert len(actions) > 0
        assert len(actions) <= 3
        # Actions should be ordered by priority
        for i, action in enumerate(actions):
            assert action["prioridade"] == i + 1

    def test_no_actions_for_no_income(self):
        """Sem renda → sem acoes."""
        result = calculate_health_score(
            renda=0, expenses=[], daily_expenses=[],
            installment_groups=[], daily_expense_history=[],
            prev_month_comprometimento=None, mes_atual=date(2026, 3, 1),
        )
        actions = generate_actions(result, 0, [], [], [])
        assert actions == []

    def test_no_actions_for_perfect_score(self, db, test_user):
        """Score perfeito → sem acoes (ou poucas)."""
        result = calculate_health_score(
            renda=10000.00, expenses=[], daily_expenses=[],
            installment_groups=[], daily_expense_history=[],
            prev_month_comprometimento=None, mes_atual=date(2026, 3, 1),
        )
        actions = generate_actions(result, 10000.00, [], [], [])
        # With perfect score, most dimensions are at 80%+, so few actions
        assert len(actions) <= 1
