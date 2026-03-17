"""
CR-032: Testes do servico de analise financeira por IA.
Testa coletor de dados, builder de prompt, cliente API (mock) e merger de acoes.
"""
import json
import pytest
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from app.models import Expense, Income, DailyExpense, ExpenseStatus
from app.ai_analysis import (
    has_minimum_data,
    build_prompts,
    call_anthropic_api,
    merge_actions,
    _parse_ai_json,
)


# ========== Fixtures ==========

VALID_AI_RESPONSE = {
    "diagnostico": {
        "resumo_geral": "Situação financeira estável com oportunidades de melhoria.",
        "comparativo_benchmark": "Gastos fixos acima do ideal (50/30/20).",
        "variacao_vs_mes_anterior": "Leve melhora no comprometimento.",
        "categorias_destaque": [
            {
                "categoria": "Moradia",
                "percentual_renda": 25.0,
                "benchmark_saudavel": 30.0,
                "variacao_mensal_percentual": -2.0,
                "observacao": "Dentro do esperado"
            }
        ]
    },
    "alertas": [
        {
            "tipo": "atencao",
            "titulo": "Comprometimento elevado",
            "descricao": "Seus gastos fixos comprometem mais de 60% da renda.",
            "impacto_mensal": 500.0,
            "impacto_anual": 6000.0
        }
    ],
    "bons_comportamentos": [
        {
            "comportamento": "Registro frequente de gastos diários",
            "mensagem_reforco": "Continue registrando! Visibilidade é o primeiro passo."
        }
    ],
    "recomendacoes": [
        {
            "prioridade": 1,
            "acao": "Revisar assinaturas de streaming",
            "justificativa": "3 assinaturas somam R$ 150/mês.",
            "economia_estimada_mensal": 50.0,
            "dificuldade": "fácil",
            "impacto_score_estimado": 3
        },
        {
            "prioridade": 2,
            "acao": "Negociar taxa do empréstimo",
            "justificativa": "Taxa atual acima da média de mercado.",
            "economia_estimada_mensal": 200.0,
            "dificuldade": "moderada",
            "impacto_score_estimado": 5
        }
    ],
    "metas": {
        "curto_prazo": {
            "descricao": "Criar reserva de emergência de R$ 1.000",
            "valor_alvo": 1000.0,
            "prazo_meses": 3,
            "primeiro_passo": "Separar R$ 350/mês automaticamente"
        },
        "medio_prazo": {
            "descricao": "Quitar parcela do notebook",
            "valor_alvo": 2400.0,
            "prazo_meses": 6,
            "primeiro_passo": "Manter pagamentos em dia"
        },
        "longo_prazo": {
            "descricao": "Reduzir comprometimento para 50%",
            "valor_alvo": 0.0,
            "prazo_meses": 12,
            "primeiro_passo": "Eliminar 1 gasto fixo não essencial"
        }
    },
    "gastos_recorrentes_disfarcados": [
        {
            "descricao": "iFood",
            "frequencia_mensal": 15,
            "valor_medio_mensal": 450.0,
            "sugestao": "Considere incluir como gasto planejado de Alimentação"
        }
    ],
    "mensagem_motivacional": "Você está no caminho certo! Manter o registro diário já é um grande passo."
}


# ========== has_minimum_data ==========

class TestHasMinimumData:
    def test_sufficient_daily_expenses(self, db, test_user):
        """7+ dias de gastos diarios = dados suficientes."""
        mes = date(2026, 2, 1)
        for day in range(1, 10):  # 9 dias
            db.add(DailyExpense(
                user_id=test_user.id, mes_referencia=mes,
                descricao=f"Gasto {day}", valor=50.0,
                data=date(2026, 2, day), categoria="Alimentação",
                subcategoria="Restaurante", metodo_pagamento="Pix",
            ))
        db.commit()
        assert has_minimum_data(db, test_user.id, mes) is True

    def test_sufficient_planned_expenses(self, db, test_user):
        """5+ despesas planejadas = dados suficientes."""
        mes = date(2026, 2, 1)
        for i in range(6):
            db.add(Expense(
                user_id=test_user.id, mes_referencia=mes,
                nome=f"Despesa {i}", valor=100.0,
                vencimento=date(2026, 2, 10), recorrente=True,
                status=ExpenseStatus.PENDENTE.value,
            ))
        db.commit()
        assert has_minimum_data(db, test_user.id, mes) is True

    def test_insufficient_data(self, db, test_user):
        """Menos de 7 dias e menos de 5 despesas = insuficiente."""
        mes = date(2026, 2, 1)
        # 3 dias de gastos diarios
        for day in range(1, 4):
            db.add(DailyExpense(
                user_id=test_user.id, mes_referencia=mes,
                descricao=f"Gasto {day}", valor=50.0,
                data=date(2026, 2, day), categoria="Alimentação",
                subcategoria="Restaurante", metodo_pagamento="Pix",
            ))
        # 2 despesas planejadas
        for i in range(2):
            db.add(Expense(
                user_id=test_user.id, mes_referencia=mes,
                nome=f"Despesa {i}", valor=100.0,
                vencimento=date(2026, 2, 10), recorrente=True,
                status=ExpenseStatus.PENDENTE.value,
            ))
        db.commit()
        assert has_minimum_data(db, test_user.id, mes) is False

    def test_empty_month(self, db, test_user):
        """Mes vazio = insuficiente."""
        mes = date(2026, 2, 1)
        assert has_minimum_data(db, test_user.id, mes) is False


# ========== build_prompts ==========

class TestBuildPrompts:
    def test_interpolation(self):
        """Prompts devem ter placeholders substituidos."""
        data = {
            "prompt_data": {
                "score_total": 50,
                "classificacao": "Estável",
                "d1": 12, "d1_detalhe": "Comprometimento alto",
                "d2": 17, "d2_detalhe": "Pressão controlada",
                "d3": 0, "d3_detalhe": "Sem poupança",
                "d4": 21, "d4_detalhe": "Bom comportamento",
                "score_conservador": 45,
                "historico_scores": "2026-01: 55 (Estável)",
                "mes_referencia": "fevereiro/2026",
                "renda_liquida": "5000.00",
                "total_planejados": "3000.00",
                "total_nao_planejados": "1000.00",
                "total_parcelas": "500.00",
                "saldo_restante": "1000.00",
                "dias_registro": 15,
                "breakdown_categorias": "Moradia: R$ 2000.00",
                "lista_gastos_planejados": "Aluguel: R$ 2000.00",
                "lista_gastos_nao_planejados": "iFood: R$ 50.00",
                "lista_parcelas": "Celular: R$ 200.00",
                "projecao_3_meses": "Dados indisponíveis",
                "comparativo_ultimos_meses": "2026-01: Renda 5000",
            }
        }
        system, user = build_prompts(data)

        # System prompt deve ser carregado
        assert "consultor financeiro" in system.lower()

        # User prompt deve ter valores substituidos
        assert "50/100" in user
        assert "Estável" in user
        assert "5000.00" in user
        assert "{{" not in user  # Nenhum placeholder restante


# ========== _parse_ai_json ==========

class TestParseAiJson:
    def test_valid_json(self):
        """JSON valido deve ser parseado corretamente."""
        result = _parse_ai_json(json.dumps(VALID_AI_RESPONSE))
        assert result["diagnostico"]["resumo_geral"] is not None

    def test_json_with_markdown_wrapper(self):
        """JSON envolto em ```json deve ser parseado."""
        wrapped = f"```json\n{json.dumps(VALID_AI_RESPONSE)}\n```"
        result = _parse_ai_json(wrapped)
        assert result["diagnostico"]["resumo_geral"] is not None

    def test_truncated_json_repair(self):
        """JSON truncado com chaves faltando deve ser reparado."""
        truncated = '{"diagnostico": {"resumo_geral": "Teste"}'  # Missing outer }
        result = _parse_ai_json(truncated)
        assert result["diagnostico"]["resumo_geral"] == "Teste"

    def test_invalid_json_raises(self):
        """JSON completamente invalido deve levantar erro."""
        with pytest.raises(json.JSONDecodeError):
            _parse_ai_json("isso nao e json de jeito nenhum")


# ========== call_anthropic_api ==========

class TestCallAnthropicApi:
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test", "CLAUDE_MODEL": "claude-test"})
    @patch("app.ai_analysis.anthropic_sdk")
    def test_success(self, mock_anthropic_module):
        """Chamada bem-sucedida deve retornar resultado parseado."""
        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(VALID_AI_RESPONSE))]
        mock_response.usage.input_tokens = 1500
        mock_response.usage.output_tokens = 800
        mock_client.messages.create.return_value = mock_response

        result = call_anthropic_api("system", "user")

        assert result["resultado"]["diagnostico"]["resumo_geral"] is not None
        assert result["tokens_input"] == 1500
        assert result["tokens_output"] == 800
        assert result["modelo"] == "claude-test"
        assert result["tempo_processamento_ms"] >= 0

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "", "CLAUDE_MODEL": "claude-test"})
    def test_missing_api_key(self):
        """Sem API key deve levantar ValueError."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            call_anthropic_api("system", "user")

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    @patch("app.ai_analysis.anthropic_sdk")
    def test_api_error_retries(self, mock_anthropic_module):
        """Erro na API deve tentar retry antes de falhar."""
        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            call_anthropic_api("system", "user")

        # Deve ter tentado 3 vezes (1 + 2 retries)
        assert mock_client.messages.create.call_count == 3

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"})
    @patch("app.ai_analysis.anthropic_sdk")
    def test_invalid_json_response(self, mock_anthropic_module):
        """Resposta nao-JSON deve retornar erro apos retries."""
        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Isso não é JSON")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_response

        with pytest.raises(ValueError, match="JSON inválido"):
            call_anthropic_api("system", "user")


# ========== merge_actions ==========

class TestMergeActions:
    def test_ia_only(self):
        """Apenas recomendacoes da IA."""
        ia_recs = [
            {"acao": "Revisar streaming", "justificativa": "Economize", "impacto_score_estimado": 5,
             "economia_estimada_mensal": 50, "dificuldade": "fácil"},
        ]
        result = merge_actions([], ia_recs)
        assert len(result) == 1
        assert result[0]["fonte"] == "ia"
        assert result[0]["acao"] == "Revisar streaming"

    def test_f04_only(self):
        """Apenas acoes da F04 (sem IA)."""
        f04 = [
            {"dimensao_alvo": "d1_comprometimento", "descricao": "Reduzir fixos", "impacto_estimado": 5},
            {"dimensao_alvo": "d3_poupanca", "descricao": "Aumentar poupança", "impacto_estimado": 3},
        ]
        result = merge_actions(f04, [])
        assert len(result) == 2
        assert all(r["fonte"] == "score" for r in result)

    def test_deduplication_ia_prevails(self):
        """IA deve prevalecer quando cobre a mesma dimensao da F04."""
        f04 = [
            {"dimensao_alvo": "d1_comprometimento", "descricao": "Reduzir fixos", "impacto_estimado": 3},
            {"dimensao_alvo": "d4_comportamento", "descricao": "Registrar gastos", "impacto_estimado": 2},
        ]
        ia_recs = [
            {"acao": "Cancelar despesa fixa X para reduzir comprometimento",
             "justificativa": "Economia imediata", "impacto_score_estimado": 5,
             "economia_estimada_mensal": 200, "dificuldade": "fácil"},
        ]
        result = merge_actions(f04, ia_recs)
        # IA cobre d1_comprometimento, F04 d4 deve passar
        assert any(r["fonte"] == "ia" for r in result)
        assert any(r["fonte"] == "score" and "Registrar" in r["acao"] for r in result)

    def test_ordering_by_impact(self):
        """Resultado deve ser ordenado por impacto decrescente."""
        ia_recs = [
            {"acao": "Ação A", "justificativa": "", "impacto_score_estimado": 2,
             "economia_estimada_mensal": 0, "dificuldade": "fácil"},
            {"acao": "Ação B", "justificativa": "", "impacto_score_estimado": 8,
             "economia_estimada_mensal": 0, "dificuldade": "fácil"},
        ]
        result = merge_actions([], ia_recs)
        assert result[0]["impacto_score"] >= result[1]["impacto_score"]

    def test_limit_to_5(self):
        """Resultado deve ser limitado a 5 acoes."""
        ia_recs = [
            {"acao": f"Ação {i}", "justificativa": "", "impacto_score_estimado": i,
             "economia_estimada_mensal": 0, "dificuldade": "fácil"}
            for i in range(8)
        ]
        result = merge_actions([], ia_recs)
        assert len(result) == 5
