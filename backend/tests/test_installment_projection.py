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
    - Celular: 12x, 3 pagas, 9 restantes (venc Mar a Dez) → Ativa
    - Sofa: 6x, 1 paga, 5 restantes (venc Mar a Ago) → Ativa
    Todas as 3 tem vencimento em Mar (PAGO ou PENDENTE) → contribuem em Mar.
    """
    parcelas = []

    # Notebook: 10x, 8 pagas (Jan-Ago 2025) + 2 pendentes (Mar, Abr 2026)
    for i in range(1, 11):
        if i <= 8:
            venc = date(2025, i, 15)
        else:
            month = i - 8 + 2  # 9->3, 10->4
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
    # Parcela 3 (Mar) PAGO → tem vencimento Mar → mes_inicio = Mar
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
    # Parcela 1 (Mar) PAGO → tem vencimento Mar → mes_inicio = Mar
    for i in range(1, 7):
        month = i + 2  # Mar=3, Abr=4, ...Ago=8
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
    """Parcelas pendentes (nenhuma paga) — vencimentos Abr-Jun (nenhum em Mar)."""
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
    CR-022: Parcelas criadas upfront (todas de uma vez).
    - Emprestimo: 10x, vencimentos Jan-Out 2026
    - 4 pagas (Jan-Abr), 6 pendentes (Mai-Out)
    - Tem vencimento em Mar (PAGO) → mes_inicio = Mar
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
        """Verifica KPIs com multiplas parcelas ativas. Todas contribuem em Mar."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        # 3 parcelas ativas: Notebook (Encerrando), Celular (Ativa), Sofa (Ativa)
        assert result["qtd_parcelas_ativas"] == 3

        # CR-024 fix: Todas tem vencimento em Mar (PAGO ou PENDENTE) → contribuem
        # Notebook 500 + Celular 300 + Sofa 400 = 1200
        assert result["total_comprometido_mes_atual"] == 1200.0

        # Renda = 10000
        assert result["renda_atual"] == 10000.0

        # Percentual = 1200 / 10000 * 100 = 12.0%
        assert result["percentual_renda_comprometida"] == 12.0

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
        """CR-024: Projecao mensal com todas contribuindo em Mar, Notebook encerra em Abr."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        projecao = result["projecao_mensal"]
        assert len(projecao) == 12

        # Mes 0 (Mar): todas ativas = 500+300+400 = 1200
        assert projecao[0]["total_comprometido"] == 1200.0
        assert projecao[0]["parcelas_ativas"] == 3

        # Mes 1 (Abr): ainda todas ativas = 1200
        assert projecao[1]["total_comprometido"] == 1200.0
        assert projecao[1]["parcelas_ativas"] == 3

        # Notebook encerra em Abr (ultimo vencimento)
        assert "Notebook" in projecao[1]["parcelas_encerrando"]

        # Mes 2 (Mai): Notebook encerrou → Celular + Sofa = 300+400=700
        assert projecao[2]["total_comprometido"] == 700.0
        assert projecao[2]["parcelas_ativas"] == 2

    def test_valor_liberado(self, mock_date, db, test_user, income_march, multiple_installments):
        """Valor liberado deve refletir diferenca entre meses consecutivos."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        projecao = result["projecao_mensal"]
        # Mes 0 (Mar): valor_liberado = 0 (primeiro mes)
        assert projecao[0]["valor_liberado"] == 0.0

        # Mes 1 (Abr): 1200 vs 1200 → 0 liberado
        assert projecao[1]["valor_liberado"] == 0.0

        # Mes 2 (Mai): Notebook ends → 1200 - 700 = 500 liberados
        assert projecao[2]["valor_liberado"] == 500.0

    def test_zero_paid_installment_with_future_start(self, mock_date, db, test_user, income_march, pending_installment):
        """CR-024: Parcela com vencimentos apenas futuros (Abr+) NAO contribui em Mar."""
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

    def test_upfront_installments_with_current_month_paid(
        self, mock_date, db, test_user, income_march, installments_all_upfront
    ):
        """CR-024 fix: Parcela com vencimento em Mar (PAGO) ainda contribui na projecao de Mar."""
        self._mock_today(mock_date)
        result = get_installment_projection(db, test_user.id)

        # Emprestimo: vencimentos Jan-Out, 4 pagas (Jan-Abr), 6 pendentes (Mai-Out)
        # Tem vencimento em Mar (PAGO) → mes_inicio = Mar (primeiro vencimento >= mes_atual)
        assert result["qtd_parcelas_ativas"] == 1

        # Contribui em Mar porque tem vencimento em Mar
        assert result["total_comprometido_mes_atual"] == 500.0
        assert result["total_restante_todas_parcelas"] == 3000.0  # 6 * 500

        # Deve ter badge Ativa (6 restantes > 2)
        assert len(result["parcelas"]) == 1
        p = result["parcelas"][0]
        assert p["status_badge"] == "Ativa"
        assert p["parcela_atual"] == 4
        assert p["mes_inicio"] == date(2026, 3, 1)  # Mar (tem vencimento Mar)
        assert p["mes_termino"] == date(2026, 10, 1)  # Out

    def test_incremental_with_current_month_paid(
        self, mock_date, db, test_user, income_march
    ):
        """CR-024 fix: Parcela incremental com Mar PAGO contribui em Mar."""
        self._mock_today(mock_date)
        # Empr. Sonia: 11x, parcelas 10 (Mar PAGO) e 11 (Abr PENDENTE)
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

        assert result["qtd_parcelas_ativas"] == 1

        # mes_inicio = Mar (tem vencimento Mar PAGO), contribui em Mar
        assert result["total_comprometido_mes_atual"] == 500.0
        assert result["total_restante_todas_parcelas"] == 500.0

        p = result["parcelas"][0]
        assert p["status_badge"] == "Encerrando"
        assert p["parcela_atual"] == 10
        assert p["mes_inicio"] == date(2026, 3, 1)  # Mar (vencimento Mar existe)
        assert p["mes_termino"] == date(2026, 4, 1)  # Abr

        # Projecao: contribui em Mar E Abr
        projecao = result["projecao_mensal"]
        assert projecao[0]["total_comprometido"] == 500.0   # Mar
        assert projecao[1]["total_comprometido"] == 500.0   # Abr
        assert projecao[2]["total_comprometido"] == 0.0     # Mai

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

        assert result["qtd_parcelas_ativas"] == 1
        # mes_inicio = Mar (1a parcela com vencimento >= mes_atual), contribui em Mar
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

    def test_concluded_installment_with_current_month_vencimento(
        self, mock_date, db, test_user, income_march
    ):
        """Parcela concluida com vencimento em Mar deve aparecer na projecao de Mar."""
        self._mock_today(mock_date)
        # Seguro do Carro: 10x incremental, parcelas 8-10 no banco, todas PAGO
        parcelas = [
            Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 1, 1),
                nome="Seguro do Carro",
                valor=511.80,
                vencimento=date(2026, 1, 19),
                parcela_atual=8,
                parcela_total=10,
                recorrente=False,
                status=ExpenseStatus.PAGO.value,
            ),
            Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 2, 1),
                nome="Seguro do Carro",
                valor=511.80,
                vencimento=date(2026, 2, 19),
                parcela_atual=9,
                parcela_total=10,
                recorrente=False,
                status=ExpenseStatus.PAGO.value,
            ),
            Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 3, 1),
                nome="Seguro do Carro",
                valor=511.80,
                vencimento=date(2026, 3, 19),
                parcela_atual=10,
                parcela_total=10,
                recorrente=False,
                status=ExpenseStatus.PAGO.value,
            ),
        ]
        for p in parcelas:
            db.add(p)
        db.commit()

        result = get_installment_projection(db, test_user.id)

        # Aparece na projecao (incluida em parcelas)
        assert len(result["parcelas"]) == 1
        p = result["parcelas"][0]
        assert p["nome"] == "Seguro do Carro"
        assert p["parcelas_restantes"] == 0
        assert p["mes_inicio"] == date(2026, 3, 1)
        assert p["mes_termino"] == date(2026, 3, 1)
        assert p["status_badge"] == "Encerrando"

        # Contribui em Mar no grafico
        assert result["total_comprometido_mes_atual"] == 511.80

        # KPIs: nao conta como "ativa" nem "restante" (ja concluida)
        assert result["qtd_parcelas_ativas"] == 0
        assert result["total_restante_todas_parcelas"] == 0.0

        # Projecao: contribui apenas em Mar
        projecao = result["projecao_mensal"]
        assert projecao[0]["total_comprometido"] == 511.80   # Mar
        assert projecao[1]["total_comprometido"] == 0.0       # Abr

    def test_concluded_installment_past_month_excluded(
        self, mock_date, db, test_user
    ):
        """Parcela concluida sem vencimento em Mar (todas antes) nao aparece."""
        self._mock_today(mock_date)
        # Parcela concluida em Fev (sem vencimento em Mar)
        parcelas = [
            Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 1, 1),
                nome="Parcela Antiga",
                valor=200.00,
                vencimento=date(2026, 1, 15),
                parcela_atual=1,
                parcela_total=2,
                recorrente=False,
                status=ExpenseStatus.PAGO.value,
            ),
            Expense(
                user_id=test_user.id,
                mes_referencia=date(2026, 2, 1),
                nome="Parcela Antiga",
                valor=200.00,
                vencimento=date(2026, 2, 15),
                parcela_atual=2,
                parcela_total=2,
                recorrente=False,
                status=ExpenseStatus.PAGO.value,
            ),
        ]
        for p in parcelas:
            db.add(p)
        db.commit()

        result = get_installment_projection(db, test_user.id)

        # Nao aparece (concluida antes de Mar)
        assert len(result["parcelas"]) == 0
        assert result["total_comprometido_mes_atual"] == 0.0
