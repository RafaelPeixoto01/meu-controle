"""
CR-021: Testes do servico de projecao de parcelas futuras.
"""
import pytest
from datetime import date
from unittest.mock import patch

from app.models import Expense, Income, ExpenseStatus
from app.services import get_installment_projection


@pytest.fixture
def income_march(db, test_user):
    """Receita de marco 2026 para calculo de percentual."""
    income = Income(
        user_id=test_user.id,
        mes_referencia=date(2026, 3, 1),
        nome="Salario",
        valor=10000.00,
        data=date(2026, 3, 5),
        recorrente=True,
    )
    db.add(income)
    db.commit()
    return income


@pytest.fixture
def multiple_installments(db, test_user):
    """
    Cenario com 3 parcelas ativas em estagios diferentes.
    Todas as parcelas criadas upfront (como a API real faz).
    - Notebook: 10x, 8 pagas, 2 restantes → Encerrando
    - Celular: 12x, 3 pagas, 9 restantes → Ativa
    - Sofa: 6x, 1 paga, 5 restantes → Ativa
    """
    parcelas = []

    # Notebook: 10x, 8 pagas + 2 pendentes
    for i in range(1, 11):
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Notebook",
            valor=500.00,
            vencimento=date(2026, 3, 15),
            parcela_atual=i,
            parcela_total=10,
            recorrente=False,
            status=ExpenseStatus.PAGO.value if i <= 8 else ExpenseStatus.PENDENTE.value,
        ))

    # Celular: 12x, 3 pagas + 9 pendentes
    for i in range(1, 13):
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Celular",
            valor=300.00,
            vencimento=date(2026, 3, 10),
            parcela_atual=i,
            parcela_total=12,
            recorrente=False,
            status=ExpenseStatus.PAGO.value if i <= 3 else ExpenseStatus.PENDENTE.value,
        ))

    # Sofa: 6x, 1 paga + 5 pendentes
    for i in range(1, 7):
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Sofa",
            valor=400.00,
            vencimento=date(2026, 3, 20),
            parcela_atual=i,
            parcela_total=6,
            recorrente=False,
            status=ExpenseStatus.PAGO.value if i <= 1 else ExpenseStatus.PENDENTE.value,
        ))

    for p in parcelas:
        db.add(p)
    db.commit()
    return parcelas


@pytest.fixture
def pending_installment(db, test_user):
    """Parcelas pendentes (nenhuma paga) — nao iniciada."""
    parcelas = []
    for i in range(1, 4):
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Emprestimo Itau",
            valor=2700.00,
            vencimento=date(2026, 3, 15),
            parcela_atual=i,
            parcela_total=3,
            recorrente=False,
            status=ExpenseStatus.PENDENTE.value,
        ))
    for p in parcelas:
        db.add(p)
    db.commit()
    return parcelas


@pytest.fixture
def installments_all_upfront(db, test_user):
    """
    CR-022: Parcelas criadas upfront (todas de uma vez, como a API real faz).
    - Emprestimo: 10x, 4 pagas (PAGO), 6 pendentes
    """
    parcelas = []
    for i in range(1, 11):
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 3, 1),
            nome="Emprestimo",
            valor=500.00,
            vencimento=date(2026, 3, 15),
            parcela_atual=i,
            parcela_total=10,
            recorrente=False,
            status=ExpenseStatus.PAGO.value if i <= 4 else ExpenseStatus.PENDENTE.value,
        ))
    for p in parcelas:
        db.add(p)
    db.commit()
    return parcelas


@patch("app.services.date")
class TestInstallmentProjection:
    """Testes do servico get_installment_projection."""

    def _mock_today(self, mock_date, today=date(2026, 3, 14)):
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *a, **kw: date(*a, **kw)

    def test_no_installments(self, mock_date, db, test_user):
        """Sem parcelas: todos os KPIs zerados, arrays vazios."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        assert result["total_comprometido_mes_atual"] == 0.0
        assert result["total_restante_todas_parcelas"] == 0.0
        assert result["qtd_parcelas_ativas"] == 0
        assert result["proxima_a_encerrar"] is None
        assert result["liberacao_proximos_3_meses"] == 0.0
        assert result["percentual_renda_comprometida"] == 0.0
        assert len(result["projecao_mensal"]) == 12
        assert len(result["parcelas"]) == 0

    def test_multiple_installments_kpis(self, mock_date, db, test_user, income_march, multiple_installments):
        """Verifica KPIs com multiplas parcelas ativas."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        # 3 parcelas ativas: Notebook (Encerrando), Celular (Ativa), Sofa (Ativa)
        assert result["qtd_parcelas_ativas"] == 3

        # Total comprometido mes atual = 500 + 300 + 400 = 1200
        assert result["total_comprometido_mes_atual"] == 1200.0

        # Renda = 10000
        assert result["renda_atual"] == 10000.0

        # Percentual = 1200 / 10000 * 100 = 12.0%
        assert result["percentual_renda_comprometida"] == 12.0

    def test_proxima_a_encerrar(self, mock_date, db, test_user, income_march, multiple_installments):
        """Proxima a encerrar deve ser Notebook (2 parcelas restantes)."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        assert result["proxima_a_encerrar"] is not None
        assert result["proxima_a_encerrar"]["nome"] == "Notebook"

    def test_status_badges(self, mock_date, db, test_user, income_march, multiple_installments):
        """Verifica atribuicao de badges: Encerrando, Ativa."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        parcelas_by_name = {p["nome"]: p for p in result["parcelas"]}
        assert parcelas_by_name["Notebook"]["status_badge"] == "Encerrando"
        assert parcelas_by_name["Celular"]["status_badge"] == "Ativa"
        assert parcelas_by_name["Sofa"]["status_badge"] == "Ativa"

    def test_projecao_mensal_decreasing(self, mock_date, db, test_user, income_march, multiple_installments):
        """Projecao mensal deve diminuir conforme parcelas encerram."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        projecao = result["projecao_mensal"]
        assert len(projecao) == 12

        # Mes 0 (marco): todos ativos = 1200
        assert projecao[0]["total_comprometido"] == 1200.0
        assert projecao[0]["parcelas_ativas"] == 3

        # Notebook tem 2 restantes, encerrando no offset 1
        assert "Notebook" in projecao[1]["parcelas_encerrando"]

        # Apos Notebook encerrar (offset 2), total = 300 + 400 = 700
        assert projecao[2]["total_comprometido"] == 700.0

    def test_valor_liberado(self, mock_date, db, test_user, income_march, multiple_installments):
        """Valor liberado deve refletir diferenca entre meses consecutivos."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        projecao = result["projecao_mensal"]
        # Mes 0: valor_liberado = 0 (primeiro mes)
        assert projecao[0]["valor_liberado"] == 0.0

        # Quando Notebook encerra (offset 2), 500 sao liberados
        assert projecao[2]["valor_liberado"] == 500.0

    def test_zero_paid_installment_included_in_projection(self, mock_date, db, test_user, income_march, pending_installment):
        """CR-023: Parcela com 0 pagas deve ser incluida na projecao como Ativa."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        # Com 0 pagas, todas as 3 parcelas restantes → Ativa (3 > 2)
        assert result["total_comprometido_mes_atual"] == 2700.0
        assert result["qtd_parcelas_ativas"] == 1

        assert len(result["parcelas"]) == 1
        assert result["parcelas"][0]["status_badge"] == "Ativa"
        assert result["parcelas"][0]["mes_termino"] is not None

    def test_no_income_no_division_error(self, mock_date, db, test_user, multiple_installments):
        """Sem renda cadastrada: percentual deve ser 0, sem erro de divisao."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        assert result["renda_atual"] == 0.0
        assert result["percentual_renda_comprometida"] == 0.0

    def test_custom_months_param(self, mock_date, db, test_user, multiple_installments):
        """Parametro months customizado deve retornar quantidade correta de pontos."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id, months=6)

        assert len(result["projecao_mensal"]) == 6

    def test_total_restante(self, mock_date, db, test_user, income_march, multiple_installments):
        """Total restante = soma de (parcelas_restantes * valor_mensal) para nao-pendentes."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        # Notebook: 2 * 500 = 1000
        # Celular: 9 * 300 = 2700
        # Sofa: 5 * 400 = 2000
        # Total = 5700
        assert result["total_restante_todas_parcelas"] == 5700.0

    def test_liberacao_proximos_3_meses(self, mock_date, db, test_user, income_march, multiple_installments):
        """Liberacao proximos 3 meses = soma de valor_liberado nos offsets 1, 2, 3."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        projecao = result["projecao_mensal"]
        expected = sum(projecao[i]["valor_liberado"] for i in range(1, 4))
        assert result["liberacao_proximos_3_meses"] == expected

    def test_upfront_installments_kpis(
        self, mock_date, db, test_user, income_march, installments_all_upfront
    ):
        """CR-022: Parcelas criadas upfront devem ter KPIs corretos via contagem PAGO."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        # 4 parcelas pagas de 10 → 6 restantes, grupo deve estar ativo
        assert result["qtd_parcelas_ativas"] == 1
        assert result["total_comprometido_mes_atual"] == 500.0
        assert result["total_restante_todas_parcelas"] == 3000.0  # 6 * 500

        # Deve ter badge Ativa (6 restantes > 2)
        assert len(result["parcelas"]) == 1
        assert result["parcelas"][0]["status_badge"] == "Ativa"
        assert result["parcelas"][0]["parcela_atual"] == 4  # inferido das pagas

        # Percentual renda = 500 / 10000 * 100 = 5%
        assert result["percentual_renda_comprometida"] == 5.0

    def test_incremental_installments_kpis(
        self, mock_date, db, test_user, income_march
    ):
        """CR-022: Parcelas incrementais (apenas recentes no banco) devem usar max(parcela_atual)."""
        self._mock_today(mock_date)
        # Empr. Sonia: 11x, apenas parcelas 10 e 11 no banco
        # Parcela 10 paga, parcela 11 pendente → restantes = 1
        parcelas = [
            Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 3, 1),
                nome="Empr. Sonia",
                valor=500.00,
                vencimento=date(2026, 3, 14),
                parcela_atual=10,
                parcela_total=11,
                recorrente=False,
                status=ExpenseStatus.PAGO.value,
            ),
            Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 4, 1),
                nome="Empr. Sonia",
                valor=500.00,
                vencimento=date(2026, 4, 14),
                parcela_atual=11,
                parcela_total=11,
                recorrente=False,
                status=ExpenseStatus.PENDENTE.value,
            ),
        ]
        for p in parcelas:
            db.add(p)
        db.commit()

        result = get_installment_projection(db, test_user.id)

        # Incremental: max_parcela_atual=10, restantes=11-10=1
        assert result["qtd_parcelas_ativas"] == 1
        assert result["total_comprometido_mes_atual"] == 500.0
        assert result["total_restante_todas_parcelas"] == 500.0  # 1 * 500

        # Encerra em 1 mes → Encerrando
        assert result["parcelas"][0]["status_badge"] == "Encerrando"
        assert result["parcelas"][0]["parcela_atual"] == 10

    def test_all_unpaid_is_active(
        self, mock_date, db, test_user
    ):
        """CR-023: Parcelas sem nenhuma paga devem ser Ativa e incluidas nos KPIs."""
        self._mock_today(mock_date)
        parcelas = []
        for i in range(1, 6):
            parcelas.append(Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 3, 1),
                nome="Futuro",
                valor=200.00,
                vencimento=date(2026, 3, 15),
                parcela_atual=i,
                parcela_total=5,
                recorrente=False,
                status=ExpenseStatus.PENDENTE.value,
            ))
        for p in parcelas:
            db.add(p)
        db.commit()

        result = get_installment_projection(db, test_user.id)

        # Nenhuma paga → Ativa (5 restantes > 2) e incluida nos KPIs
        assert result["qtd_parcelas_ativas"] == 1
        assert result["total_comprometido_mes_atual"] == 200.0
        assert len(result["parcelas"]) == 1
        assert result["parcelas"][0]["status_badge"] == "Ativa"
        assert result["parcelas"][0]["mes_termino"] is not None
