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
    Cenario com 3 parcelas ativas em estagios diferentes:
    - Notebook: parcela 8 de 10 (faltam 2 → Encerrando)
    - Celular: parcela 3 de 12 (faltam 9 → Ativa)
    - Sofa: parcela 1 de 6 (faltam 5 → Ativa)
    """
    parcelas = []

    # Notebook: 10x, atualmente em 8/10 (mes marco 2026)
    for i in range(1, 9):
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, 3 - 8 + i, 1) if (3 - 8 + i) > 0 else date(2025, 12 + (3 - 8 + i), 1),
            nome="Notebook",
            valor=500.00,
            vencimento=date(2026, 3, 15),
            parcela_atual=i,
            parcela_total=10,
            recorrente=False,
            status=ExpenseStatus.PAGO.value if i < 8 else ExpenseStatus.PENDENTE.value,
        ))

    # Celular: 12x, atualmente em 3/12 (mes marco 2026)
    for i in range(1, 4):
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, i, 1),
            nome="Celular",
            valor=300.00,
            vencimento=date(2026, 3, 10),
            parcela_atual=i,
            parcela_total=12,
            recorrente=False,
            status=ExpenseStatus.PAGO.value if i < 3 else ExpenseStatus.PENDENTE.value,
        ))

    # Sofa: 6x, atualmente em 1/6 (mes marco 2026)
    parcelas.append(Expense(
        user_id=test_user.id,
        mes_referencia=date(2026, 3, 1),
        nome="Sofa",
        valor=400.00,
        vencimento=date(2026, 3, 20),
        parcela_atual=1,
        parcela_total=6,
        recorrente=False,
        status=ExpenseStatus.PENDENTE.value,
    ))

    for p in parcelas:
        db.add(p)
    db.commit()
    return parcelas


@pytest.fixture
def pending_installment(db, test_user):
    """Parcela pendente (0 de Y) — nao iniciada."""
    p = Expense(
        user_id=test_user.id,
        mes_referencia=date(2026, 3, 1),
        nome="Emprestimo Itau",
        valor=2700.00,
        vencimento=date(2026, 3, 15),
        parcela_atual=0,
        parcela_total=60,
        recorrente=False,
        status=ExpenseStatus.PENDENTE.value,
    )
    db.add(p)
    db.commit()
    return p


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

        # Mes 2 (maio): Notebook encerra neste mes (parcela 10/10)
        # Notebook tem 2 restantes, entao no offset 1 ela esta ativa, no offset 2 ela encerrara
        assert "Notebook" in projecao[1]["parcelas_encerrando"]

        # Apos Notebook encerrar, total deve ser 700 (300 + 400)
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

    def test_pending_installment_excluded_from_total(self, mock_date, db, test_user, income_march, pending_installment):
        """Parcela pendente (0 de Y) nao deve contar no total comprometido."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        # Pendente nao conta como ativa
        assert result["total_comprometido_mes_atual"] == 0.0
        assert result["qtd_parcelas_ativas"] == 0

        # Mas aparece na lista de parcelas com badge Pendente
        assert len(result["parcelas"]) == 1
        assert result["parcelas"][0]["status_badge"] == "Pendente"
        assert result["parcelas"][0]["mes_termino"] is None

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
