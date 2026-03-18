"""
CR-033: Testes do motor de alertas inteligentes.
Testa cada checker individualmente, o engine e o gerenciamento de estado.
"""
import json
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.models import Expense, Income, ExpenseStatus, ScoreHistorico, AnaliseFinanceira, ConfiguracaoAlertas
from app.alerts import (
    VencimentoProximoChecker,
    DespesaAtrasadaChecker,
    ParcelaEncerrandoChecker,
    ScoreDeteriorandoChecker,
    ComprometimentoAltoChecker,
    ParcelaAtivadaChecker,
    AlertasIAChecker,
    AlertEngine,
)
from app import crud


# ========== Helpers ==========

def make_expense(user_id, mes, nome, valor, vencimento, status="Pendente", parcela_atual=None, parcela_total=None):
    return Expense(
        user_id=user_id, mes_referencia=mes, nome=nome, valor=valor,
        vencimento=vencimento, status=status, recorrente=True,
        parcela_atual=parcela_atual, parcela_total=parcela_total,
    )


def make_config(**overrides):
    """Cria um mock de ConfiguracaoAlertas com defaults."""
    config = MagicMock()
    config.antecedencia_vencimento = overrides.get("antecedencia_vencimento", 3)
    config.alerta_atrasadas = overrides.get("alerta_atrasadas", True)
    config.alerta_parcelas_encerrando = overrides.get("alerta_parcelas_encerrando", True)
    config.alerta_score = overrides.get("alerta_score", True)
    config.alerta_comprometimento = overrides.get("alerta_comprometimento", True)
    config.limiar_comprometimento = overrides.get("limiar_comprometimento", 50)
    config.alerta_parcela_ativada = overrides.get("alerta_parcela_ativada", True)
    config.alerta_ia = overrides.get("alerta_ia", True)
    return config


# ========== A1: Vencimento Proximo ==========

class TestVencimentoProximoChecker:
    def test_despesa_dentro_da_antecedencia(self, db, test_user):
        today = date.today()
        venc = today + timedelta(days=2)
        exp = make_expense(test_user.id, date(today.year, today.month, 1), "IPVA", 1000, venc)
        db.add(exp)
        db.commit()

        checker = VencimentoProximoChecker()
        config = make_config(antecedencia_vencimento=3)
        dados = {"today": today, "expenses": [exp], "mes_referencia": date(today.year, today.month, 1)}

        result = checker.check(dados, config)
        assert len(result) == 1
        assert result[0]["alerta_tipo"] == "A1"
        assert "IPVA" in result[0]["titulo"]
        assert "2 dias" in result[0]["titulo"]

    def test_despesa_fora_da_antecedencia(self, db, test_user):
        today = date.today()
        venc = today + timedelta(days=10)
        exp = make_expense(test_user.id, date(today.year, today.month, 1), "IPTU", 500, venc)
        db.add(exp)
        db.commit()

        checker = VencimentoProximoChecker()
        config = make_config(antecedencia_vencimento=3)
        dados = {"today": today, "expenses": [exp], "mes_referencia": date(today.year, today.month, 1)}

        result = checker.check(dados, config)
        assert len(result) == 0

    def test_despesa_paga_ignorada(self, db, test_user):
        today = date.today()
        venc = today + timedelta(days=1)
        exp = make_expense(test_user.id, date(today.year, today.month, 1), "Luz", 200, venc, status="Pago")
        db.add(exp)
        db.commit()

        checker = VencimentoProximoChecker()
        config = make_config()
        dados = {"today": today, "expenses": [exp], "mes_referencia": date(today.year, today.month, 1)}

        result = checker.check(dados, config)
        assert len(result) == 0

    def test_sem_despesas(self):
        checker = VencimentoProximoChecker()
        config = make_config()
        dados = {"today": date.today(), "expenses": [], "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, config)
        assert len(result) == 0


# ========== A2: Despesa Atrasada ==========

class TestDespesaAtrasadaChecker:
    def test_despesas_atrasadas(self, db, test_user):
        today = date.today()
        venc = today - timedelta(days=5)
        exp = make_expense(test_user.id, date(today.year, today.month, 1), "Luz", 300, venc, status="Atrasado")
        db.add(exp)
        db.commit()

        checker = DespesaAtrasadaChecker()
        config = make_config()
        dados = {"today": today, "expenses": [exp], "mes_referencia": date(today.year, today.month, 1)}

        result = checker.check(dados, config)
        assert len(result) == 1
        assert result[0]["severidade"] == "critico"
        assert "atrasada" in result[0]["titulo"]
        assert "5 dias" in result[0]["descricao"]

    def test_nenhuma_atrasada(self):
        checker = DespesaAtrasadaChecker()
        config = make_config()
        dados = {"today": date.today(), "expenses": [], "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, config)
        assert len(result) == 0

    def test_multiplas_ordenadas_por_atraso(self, db, test_user):
        today = date.today()
        exp1 = make_expense(test_user.id, date(today.year, today.month, 1), "Luz", 300,
                           today - timedelta(days=2), status="Atrasado")
        exp2 = make_expense(test_user.id, date(today.year, today.month, 1), "Internet", 150,
                           today - timedelta(days=8), status="Atrasado")
        db.add_all([exp1, exp2])
        db.commit()

        checker = DespesaAtrasadaChecker()
        dados = {"today": today, "expenses": [exp1, exp2], "mes_referencia": date(today.year, today.month, 1)}

        result = checker.check(dados, make_config())
        assert len(result) == 2
        # Mais atrasada primeiro (exp2 venceu ha 8 dias)
        assert "Internet" in result[0]["titulo"]
        assert "Luz" in result[1]["titulo"]


# ========== A3: Parcela Encerrando ==========

class TestParcelaEncerrandoChecker:
    def test_ultima_parcela(self, db, test_user):
        mes = date(2026, 3, 1)
        exp = make_expense(test_user.id, mes, "Seguro", 500, date(2026, 3, 15),
                          parcela_atual=10, parcela_total=10)
        db.add(exp)
        db.commit()

        checker = ParcelaEncerrandoChecker()
        dados = {"expenses": [exp], "mes_referencia": mes}

        result = checker.check(dados, make_config())
        assert len(result) == 1
        assert "termina este mês" in result[0]["titulo"]
        assert result[0]["severidade"] == "informativo"

    def test_penultima_parcela(self, db, test_user):
        mes = date(2026, 3, 1)
        exp = make_expense(test_user.id, mes, "Celular", 200, date(2026, 3, 10),
                          parcela_atual=9, parcela_total=10)
        db.add(exp)
        db.commit()

        checker = ParcelaEncerrandoChecker()
        dados = {"expenses": [exp], "mes_referencia": mes}

        result = checker.check(dados, make_config())
        assert len(result) == 1
        assert "próximo mês" in result[0]["titulo"]

    def test_parcela_no_inicio(self, db, test_user):
        mes = date(2026, 3, 1)
        exp = make_expense(test_user.id, mes, "TV", 300, date(2026, 3, 15),
                          parcela_atual=2, parcela_total=10)
        db.add(exp)
        db.commit()

        checker = ParcelaEncerrandoChecker()
        dados = {"expenses": [exp], "mes_referencia": mes}

        result = checker.check(dados, make_config())
        assert len(result) == 0


# ========== A4: Score Deteriorando ==========

class TestScoreDeteriorandoChecker:
    def test_queda_5_pontos(self):
        prev = MagicMock(score_total=65, d1_comprometimento=20, d2_parcelas=15,
                        d3_poupanca=15, d4_comportamento=15)
        curr = MagicMock(score_total=58, d1_comprometimento=13, d2_parcelas=15,
                        d3_poupanca=15, d4_comportamento=15)
        mes = date(2026, 3, 1)

        checker = ScoreDeteriorandoChecker()
        dados = {"score_current": curr, "score_previous": prev, "mes_referencia": mes}

        result = checker.check(dados, make_config())
        assert len(result) == 1
        assert result[0]["severidade"] == "atencao"
        assert "caiu 7 pontos" in result[0]["titulo"]
        assert "comprometimento" in result[0]["descricao"]

    def test_subida_10_pontos(self):
        prev = MagicMock(score_total=50, d1_comprometimento=10, d2_parcelas=10,
                        d3_poupanca=15, d4_comportamento=15)
        curr = MagicMock(score_total=62, d1_comprometimento=18, d2_parcelas=14,
                        d3_poupanca=15, d4_comportamento=15)
        mes = date(2026, 3, 1)

        checker = ScoreDeteriorandoChecker()
        dados = {"score_current": curr, "score_previous": prev, "mes_referencia": mes}

        result = checker.check(dados, make_config())
        assert len(result) == 1
        assert result[0]["severidade"] == "informativo"
        assert "subiu" in result[0]["titulo"]

    def test_sem_historico(self):
        checker = ScoreDeteriorandoChecker()
        dados = {"score_current": None, "score_previous": None, "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, make_config())
        assert len(result) == 0

    def test_variacao_menor_que_5(self):
        prev = MagicMock(score_total=65, d1_comprometimento=20, d2_parcelas=15,
                        d3_poupanca=15, d4_comportamento=15)
        curr = MagicMock(score_total=63, d1_comprometimento=18, d2_parcelas=15,
                        d3_poupanca=15, d4_comportamento=15)
        mes = date(2026, 3, 1)

        checker = ScoreDeteriorandoChecker()
        dados = {"score_current": curr, "score_previous": prev, "mes_referencia": mes}

        result = checker.check(dados, make_config())
        assert len(result) == 0


# ========== A5: Comprometimento Alto ==========

class TestComprometimentoAltoChecker:
    def test_acima_do_limiar(self):
        checker = ComprometimentoAltoChecker()
        dados = {"total_income": 10000, "total_expenses": 7000, "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, make_config(limiar_comprometimento=50))
        assert len(result) == 1
        assert "70" in result[0]["titulo"] or "50%" in result[0]["titulo"]

    def test_abaixo_do_limiar(self):
        checker = ComprometimentoAltoChecker()
        dados = {"total_income": 10000, "total_expenses": 4000, "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, make_config(limiar_comprometimento=50))
        assert len(result) == 0

    def test_renda_zero(self):
        checker = ComprometimentoAltoChecker()
        dados = {"total_income": 0, "total_expenses": 5000, "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, make_config())
        assert len(result) == 0


# ========== A6: Parcela Ativada ==========

class TestParcelaAtivadaChecker:
    def test_nova_parcela_ativada(self, db, test_user):
        mes = date(2026, 3, 1)
        exp_curr = make_expense(test_user.id, mes, "Empréstimo", 2000, date(2026, 3, 10),
                               parcela_atual=1, parcela_total=60)
        db.add(exp_curr)
        db.commit()

        checker = ParcelaAtivadaChecker()
        dados = {
            "expenses": [exp_curr],
            "prev_expenses": [],  # Nao existia no mes anterior
            "total_income": 10000,
            "total_expenses": 7000,
            "mes_referencia": mes,
        }

        result = checker.check(dados, make_config())
        assert len(result) == 1
        assert result[0]["severidade"] == "critico"
        assert "iniciou pagamento" in result[0]["titulo"]

    def test_parcela_ja_ativa(self, db, test_user):
        mes = date(2026, 3, 1)
        prev_mes = date(2026, 2, 1)
        exp_curr = make_expense(test_user.id, mes, "Celular", 200, date(2026, 3, 15),
                               parcela_atual=5, parcela_total=10)
        exp_prev = make_expense(test_user.id, prev_mes, "Celular", 200, date(2026, 2, 15),
                               parcela_atual=4, parcela_total=10)
        db.add_all([exp_curr, exp_prev])
        db.commit()

        checker = ParcelaAtivadaChecker()
        dados = {
            "expenses": [exp_curr],
            "prev_expenses": [exp_prev],
            "total_income": 10000,
            "total_expenses": 5000,
            "mes_referencia": mes,
        }

        result = checker.check(dados, make_config())
        assert len(result) == 0


# ========== A7+A8: Alertas IA ==========

class TestAlertasIAChecker:
    def test_com_alertas_ia(self):
        analise = MagicMock()
        analise.resultado = json.dumps({
            "alertas": [
                {"tipo": "critico", "titulo": "Cartão estourado", "descricao": "Limite baixo",
                 "impacto_mensal": 500, "impacto_anual": 6000},
            ],
            "gastos_recorrentes_disfarcados": [
                {"descricao": "iFood", "frequencia_mensal": 18, "valor_medio_mensal": 890,
                 "sugestao": "Incluir como planejado"},
            ],
        })

        checker = AlertasIAChecker()
        dados = {"analise_ia": analise, "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, make_config())
        assert len(result) == 2
        # A7
        assert result[0]["alerta_tipo"] == "A7"
        assert result[0]["severidade"] == "critico"
        # A8
        assert result[1]["alerta_tipo"] == "A8"
        assert "iFood" in result[1]["titulo"]

    def test_sem_analise_ia(self):
        checker = AlertasIAChecker()
        dados = {"analise_ia": None, "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, make_config())
        assert len(result) == 0

    def test_maximo_5_alertas(self):
        analise = MagicMock()
        alertas = [{"tipo": "informativo", "titulo": f"Alerta {i}", "descricao": f"Desc {i}",
                    "impacto_mensal": 0, "impacto_anual": 0} for i in range(8)]
        analise.resultado = json.dumps({
            "alertas": alertas,
            "gastos_recorrentes_disfarcados": [],
        })

        checker = AlertasIAChecker()
        dados = {"analise_ia": analise, "mes_referencia": date(2026, 3, 1)}

        result = checker.check(dados, make_config())
        a7_count = sum(1 for a in result if a["alerta_tipo"] == "A7")
        assert a7_count == 5  # Max 5


# ========== Engine: Checkers Desabilitados ==========

class TestAlertEngine:
    def test_checker_desabilitado(self, db, test_user):
        today = date.today()
        mes = date(today.year, today.month, 1)
        # Despesa atrasada
        exp = make_expense(test_user.id, mes, "Conta", 100, today - timedelta(days=3), status="Atrasado")
        db.add(exp)
        # Receita para evitar divisao por zero
        inc = Income(user_id=test_user.id, mes_referencia=mes, nome="Salario", valor=5000,
                    data=today, recorrente=True)
        db.add(inc)
        db.commit()

        # Desabilitar A2
        config = ConfiguracaoAlertas(user_id=test_user.id, alerta_atrasadas=False)
        db.add(config)
        db.commit()

        engine = AlertEngine()
        result = engine.calcular_alertas(db, test_user.id, mes)

        # A2 nao deve aparecer
        a2_alerts = [a for a in result["alertas"] if a["tipo"] == "A2"]
        assert len(a2_alerts) == 0

    def test_ordenacao_severidade(self, db, test_user):
        today = date.today()
        mes = date(today.year, today.month, 1)
        # Uma atrasada (critico) e uma vencendo (atencao)
        exp1 = make_expense(test_user.id, mes, "Atrasada", 100,
                           today - timedelta(days=2), status="Atrasado")
        exp2 = make_expense(test_user.id, mes, "Vencendo", 200,
                           today + timedelta(days=1), status="Pendente")
        inc = Income(user_id=test_user.id, mes_referencia=mes, nome="Salario", valor=5000,
                    data=today, recorrente=True)
        db.add_all([exp1, exp2, inc])
        db.commit()

        engine = AlertEngine()
        result = engine.calcular_alertas(db, test_user.id, mes)

        alertas = result["alertas"]
        if len(alertas) >= 2:
            # Critico deve vir antes de atencao
            criticos = [a for a in alertas if a["severidade"] == "critico"]
            atencao = [a for a in alertas if a["severidade"] == "atencao"]
            if criticos and atencao:
                critico_idx = alertas.index(criticos[0])
                atencao_idx = alertas.index(atencao[0])
                assert critico_idx < atencao_idx


# ========== State Management ==========

class TestAlertState:
    def test_dismiss_alerta(self, db, test_user):
        today = date.today()
        mes = date(today.year, today.month, 1)
        exp = make_expense(test_user.id, mes, "Luz", 200,
                          today - timedelta(days=1), status="Atrasado")
        inc = Income(user_id=test_user.id, mes_referencia=mes, nome="Salario", valor=5000,
                    data=today, recorrente=True)
        db.add_all([exp, inc])
        db.commit()

        engine = AlertEngine()

        # Primeira execucao: deve gerar alertas
        result1 = engine.calcular_alertas(db, test_user.id, mes)
        a2_alerts = [a for a in result1["alertas"] if a["tipo"] == "A2"]
        assert len(a2_alerts) >= 1

        # Dispensar o alerta
        alerta = crud.get_alerta_by_id(db, a2_alerts[0]["id"], test_user.id)
        crud.mark_alerta_dispensado(db, alerta)

        # Segunda execucao: alertas dispensados nao reaparecem
        result2 = engine.calcular_alertas(db, test_user.id, mes)
        a2_alerts2 = [a for a in result2["alertas"] if a["tipo"] == "A2"]
        assert len(a2_alerts2) == 0

    def test_auto_resolucao(self, db, test_user):
        today = date.today()
        mes = date(today.year, today.month, 1)
        exp = make_expense(test_user.id, mes, "Conta", 300,
                          today + timedelta(days=1), status="Pendente")
        inc = Income(user_id=test_user.id, mes_referencia=mes, nome="Salario", valor=5000,
                    data=today, recorrente=True)
        db.add_all([exp, inc])
        db.commit()

        engine = AlertEngine()

        # Primeira execucao: gera A1
        result1 = engine.calcular_alertas(db, test_user.id, mes)
        a1_alerts = [a for a in result1["alertas"] if a["tipo"] == "A1"]
        assert len(a1_alerts) >= 1
        alerta_id = a1_alerts[0]["id"]

        # "Pagar" a despesa
        exp.status = ExpenseStatus.PAGO.value
        db.commit()

        # Segunda execucao: A1 nao e mais gerado, alerta deve ser auto-resolvido
        result2 = engine.calcular_alertas(db, test_user.id, mes)
        a1_alerts2 = [a for a in result2["alertas"] if a["tipo"] == "A1"]
        assert len(a1_alerts2) == 0

        # Verificar que o alerta foi resolvido no banco
        alerta = crud.get_alerta_by_id(db, alerta_id, test_user.id)
        assert alerta.status == "resolvido"
