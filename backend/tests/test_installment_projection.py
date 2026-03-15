"""
CR-021: Testes do servico de projecao de parcelas futuras.
CR-024: Testes com datas de vencimento realistas para offset de inicio.
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
    CR-024: Vencimentos realistas — cada parcela em um mes diferente.
    - Notebook: 10x, 8 pagas, 2 restantes (venc Mar e Abr) → Encerrando
    - Celular: 12x, 3 pagas, 9 restantes (venc Mar a Nov) → Ativa
    - Sofa: 6x, 1 paga, 5 restantes (venc Mar a Jul) → Ativa
    """
    parcelas = []

    # Notebook: 10x, 8 pagas (Jan-Ago passado) + 2 pendentes (Mar, Abr)
    for i in range(1, 11):
        month = ((i - 1) % 12) + 1
        year = 2025 if i <= 8 else 2026
        if i <= 8:
            month = i  # Jan-Ago 2025
            venc = date(2025, month, 15)
        else:
            month = i - 8 + 2  # Mar=9->3, Abr=10->4
            venc = date(2026, month, 15)
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(venc.year, venc.month, 1),
            nome="Notebook",
            valor=500.00,
            vencimento=venc,
            parcela_atual=i,
            parcela_total=10,
            recorrente=False,
            status=ExpenseStatus.PAGO.value if i <= 8 else ExpenseStatus.PENDENTE.value,
        ))

    # Celular: 12x, 3 pagas (Jan-Mar 2026) + 9 pendentes (Abr-Dez 2026)
    # Note: parcela 3 paga em Mar, parcela 4 pendente em Abr
    for i in range(1, 13):
        venc = date(2026, i, 10)
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, i, 1),
            nome="Celular",
            valor=300.00,
            vencimento=venc,
            parcela_atual=i,
            parcela_total=12,
            recorrente=False,
            status=ExpenseStatus.PAGO.value if i <= 3 else ExpenseStatus.PENDENTE.value,
        ))

    # Sofa: 6x, 1 paga (Mar) + 5 pendentes (Abr-Ago 2026)
    for i in range(1, 7):
        month = i + 2  # Mar=1->3, Abr=2->4, ...Ago=6->8
        venc = date(2026, month, 20)
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, month, 1),
            nome="Sofa",
            valor=400.00,
            vencimento=venc,
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
    """Parcelas pendentes (nenhuma paga) — nao iniciada, vencimentos Abr-Jun."""
    parcelas = []
    for i in range(1, 4):
        month = i + 3  # Abr=4, Mai=5, Jun=6
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, month, 1),
            nome="Emprestimo Itau",
            valor=2700.00,
            vencimento=date(2026, month, 15),
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
    - Emprestimo: 10x, 4 pagas (Jan-Abr), 6 pendentes (Mai-Out)
    """
    parcelas = []
    for i in range(1, 11):
        venc = date(2026, i, 15)
        parcelas.append(Expense(
            user_id=test_user.id,
            mes_referencia=date(2026, i, 1),
            nome="Emprestimo",
            valor=500.00,
            vencimento=venc,
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

        # CR-024: Total comprometido mes atual (Marco):
        # Notebook: mes_inicio=Mar (parcela 9 pendente), contribui em Mar → 500
        # Celular: mes_inicio=Abr (parcela 4 pendente), NAO contribui em Mar → 0
        # Sofa: mes_inicio=Abr (parcela 2 pendente), NAO contribui em Mar → 0
        assert result["total_comprometido_mes_atual"] == 500.0

        # Renda = 10000
        assert result["renda_atual"] == 10000.0

        # Percentual = 500 / 10000 * 100 = 5.0%
        assert result["percentual_renda_comprometida"] == 5.0

    def test_proxima_a_encerrar(self, mock_date, db, test_user, income_march, multiple_installments):
        """Proxima a encerrar deve ser Notebook (2 parcelas restantes, termina em Abr)."""
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

    def test_projecao_mensal_with_offset(self, mock_date, db, test_user, income_march, multiple_installments):
        """CR-024: Projecao mensal deve respeitar mes_inicio de cada parcela."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        projecao = result["projecao_mensal"]
        assert len(projecao) == 12

        # Mes 0 (Marco): apenas Notebook ativo (Mar-Abr) → 500
        assert projecao[0]["total_comprometido"] == 500.0
        assert projecao[0]["parcelas_ativas"] == 1

        # Mes 1 (Abril): Notebook (Mar-Abr) + Celular (Abr-Dez) + Sofa (Abr-Ago) = 500+300+400=1200
        assert projecao[1]["total_comprometido"] == 1200.0
        assert projecao[1]["parcelas_ativas"] == 3

        # Notebook encerra em Abr (mes 1)
        assert "Notebook" in projecao[1]["parcelas_encerrando"]

        # Mes 2 (Maio): Celular + Sofa = 300+400=700
        assert projecao[2]["total_comprometido"] == 700.0
        assert projecao[2]["parcelas_ativas"] == 2

    def test_valor_liberado(self, mock_date, db, test_user, income_march, multiple_installments):
        """Valor liberado deve refletir diferenca entre meses consecutivos."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        projecao = result["projecao_mensal"]
        # Mes 0: valor_liberado = 0 (primeiro mes)
        assert projecao[0]["valor_liberado"] == 0.0

        # Mes 1 (Abr): 1200 vs 500 → valor_liberado negativo (mais gastos)
        # Actually valor_liberado = prev - current = 500 - 1200 = -700
        assert projecao[1]["valor_liberado"] == -700.0

        # Mes 2 (Mai): Notebook ends → 1200 - 700 = 500 liberados
        assert projecao[2]["valor_liberado"] == 500.0

    def test_zero_paid_installment_with_future_start(self, mock_date, db, test_user, income_march, pending_installment):
        """CR-024: Parcela com 0 pagas e vencimento futuro (Abr) NAO contribui no mes atual (Mar)."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        # Parcela com vencimentos Abr, Mai, Jun → nao contribui em Mar
        assert result["total_comprometido_mes_atual"] == 0.0
        assert result["qtd_parcelas_ativas"] == 1

        assert len(result["parcelas"]) == 1
        p = result["parcelas"][0]
        assert p["status_badge"] == "Ativa"
        assert p["mes_inicio"] == date(2026, 4, 1)
        assert p["mes_termino"] == date(2026, 6, 1)

        # Projecao: deve contribuir a partir de Abr (offset 1)
        projecao = result["projecao_mensal"]
        assert projecao[0]["total_comprometido"] == 0.0  # Mar
        assert projecao[1]["total_comprometido"] == 2700.0  # Abr
        assert projecao[2]["total_comprometido"] == 2700.0  # Mai
        assert projecao[3]["total_comprometido"] == 2700.0  # Jun
        assert projecao[4]["total_comprometido"] == 0.0  # Jul (acabou)

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
        """Total restante = soma de (parcelas_restantes * valor_mensal)."""
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

        # 4 parcelas pagas (Jan-Abr), 6 pendentes (Mai-Out)
        # mes_inicio = Mai, mes_termino = Out
        assert result["qtd_parcelas_ativas"] == 1

        # CR-024: Mai nao e o mes atual (Mar), entao nao contribui em Mar
        assert result["total_comprometido_mes_atual"] == 0.0
        assert result["total_restante_todas_parcelas"] == 3000.0  # 6 * 500

        # Deve ter badge Ativa (6 restantes > 2)
        assert len(result["parcelas"]) == 1
        p = result["parcelas"][0]
        assert p["status_badge"] == "Ativa"
        assert p["parcela_atual"] == 4  # inferido das pagas
        assert p["mes_inicio"] == date(2026, 5, 1)
        assert p["mes_termino"] == date(2026, 10, 1)

    def test_incremental_installments_kpis(
        self, mock_date, db, test_user, income_march
    ):
        """CR-022/024: Parcelas incrementais devem usar datas reais de vencimento."""
        self._mock_today(mock_date)
        # Empr. Sonia: 11x, apenas parcelas 10 e 11 no banco
        # Parcela 10 paga (Mar), parcela 11 pendente (Abr) → restantes = 1
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

        # CR-024: mes_inicio = Abr (1a nao paga), nao contribui em Mar
        assert result["total_comprometido_mes_atual"] == 0.0
        assert result["total_restante_todas_parcelas"] == 500.0  # 1 * 500

        # Encerra em 1 mes → Encerrando
        p = result["parcelas"][0]
        assert p["status_badge"] == "Encerrando"
        assert p["parcela_atual"] == 10
        assert p["mes_inicio"] == date(2026, 4, 1)
        assert p["mes_termino"] == date(2026, 4, 1)

        # Projecao: contribui apenas em Abr
        projecao = result["projecao_mensal"]
        assert projecao[0]["total_comprometido"] == 0.0    # Mar
        assert projecao[1]["total_comprometido"] == 500.0   # Abr
        assert projecao[2]["total_comprometido"] == 0.0    # Mai

    def test_all_unpaid_is_active(
        self, mock_date, db, test_user
    ):
        """CR-023/024: Parcelas sem nenhuma paga devem ser Ativa, com mes_inicio correto."""
        self._mock_today(mock_date)
        parcelas = []
        for i in range(1, 6):
            month = i + 2  # Mar=3, Abr=4, ..., Jul=7
            parcelas.append(Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, month, 1),
                nome="Futuro",
                valor=200.00,
                vencimento=date(2026, month, 15),
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
        # mes_inicio = Mar (1a parcela), contribui em Mar
        assert result["total_comprometido_mes_atual"] == 200.0
        assert len(result["parcelas"]) == 1
        p = result["parcelas"][0]
        assert p["status_badge"] == "Ativa"
        assert p["mes_inicio"] == date(2026, 3, 1)
        assert p["mes_termino"] == date(2026, 7, 1)

    def test_mes_inicio_field_present(self, mock_date, db, test_user, income_march, multiple_installments):
        """CR-024: Campo mes_inicio deve estar presente em todas as parcelas."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        for p in result["parcelas"]:
            assert "mes_inicio" in p
            assert p["mes_inicio"] is not None
            assert "mes_termino" in p
            assert p["mes_termino"] is not None
