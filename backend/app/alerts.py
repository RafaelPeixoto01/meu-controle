"""CR-033: Motor de alertas inteligentes.

Implementa 8 tipos de alertas (A1-A8) com arquitetura extensivel baseada em checkers.
Cada checker implementa BaseAlertChecker e produz alertas independentemente.
O AlertEngine orquestra a execucao e reconcilia com estado persistido.
"""
import json
import logging
from abc import ABC, abstractmethod
from datetime import date, timedelta, datetime
from typing import Any

from sqlalchemy.orm import Session

from app import crud
from app.models import ExpenseStatus
from app.services import apply_status_auto_detection, get_previous_month

logger = logging.getLogger(__name__)

SEVERITY_ORDER = {"critico": 0, "atencao": 1, "informativo": 2}


class BaseAlertChecker(ABC):
    """Interface base para checkers de alerta."""

    @property
    @abstractmethod
    def tipo(self) -> str:
        """Identificador do tipo de alerta (ex: 'A1', 'A2')."""
        pass

    @abstractmethod
    def check(self, dados: dict, config: Any) -> list[dict]:
        """Verifica condicoes e retorna lista de alertas brutos."""
        pass


class VencimentoProximoChecker(BaseAlertChecker):
    """A1: Despesas pendentes vencendo em X dias."""

    @property
    def tipo(self) -> str:
        return "A1"

    def check(self, dados: dict, config: Any) -> list[dict]:
        antecedencia = config.antecedencia_vencimento
        today = dados["today"]
        cutoff = today + timedelta(days=antecedencia)
        alertas = []

        for exp in dados["expenses"]:
            if exp.status != ExpenseStatus.PENDENTE.value:
                continue
            venc = exp.vencimento
            if isinstance(venc, datetime):
                venc = venc.date()
            if today <= venc <= cutoff:
                dias = (venc - today).days
                fonte = ""
                alertas.append({
                    "alerta_tipo": "A1",
                    "alerta_referencia": exp.id,
                    "severidade": "atencao",
                    "titulo": f"{exp.nome} vence em {dias} dia{'s' if dias != 1 else ''}",
                    "descricao": f"R$ {float(exp.valor):,.2f} com vencimento em {venc.strftime('%d/%m')}.".replace(",", "X").replace(".", ",").replace("X", "."),
                    "impacto_mensal": float(exp.valor),
                    "contexto_aba": "gastos_planejados",
                    "acao_tipo": "marcar_pago",
                    "acao_referencia_id": exp.id,
                })
        return alertas


class DespesaAtrasadaChecker(BaseAlertChecker):
    """A2: Despesas vencidas nao pagas."""

    @property
    def tipo(self) -> str:
        return "A2"

    def check(self, dados: dict, config: Any) -> list[dict]:
        today = dados["today"]
        alertas = []

        atrasadas = [e for e in dados["expenses"] if e.status == ExpenseStatus.ATRASADO.value]
        # Ordenar por dias de atraso (mais atrasada primeiro)
        atrasadas.sort(key=lambda e: e.vencimento)

        for exp in atrasadas:
            venc = exp.vencimento
            if isinstance(venc, datetime):
                venc = venc.date()
            dias_atraso = (today - venc).days
            alertas.append({
                "alerta_tipo": "A2",
                "alerta_referencia": exp.id,
                "severidade": "critico",
                "titulo": f"{exp.nome} está atrasada",
                "descricao": f"Venceu em {venc.strftime('%d/%m')} ({dias_atraso} dias atrás). Valor: R$ {float(exp.valor):,.2f}.".replace(",", "X").replace(".", ",").replace("X", "."),
                "impacto_mensal": float(exp.valor),
                "contexto_aba": "gastos_planejados",
                "acao_tipo": "marcar_pago",
                "acao_referencia_id": exp.id,
            })
        return alertas


class ParcelaEncerrandoChecker(BaseAlertChecker):
    """A3: Parcelas nas ultimas 2 prestacoes."""

    @property
    def tipo(self) -> str:
        return "A3"

    def check(self, dados: dict, config: Any) -> list[dict]:
        alertas = []
        mes = dados["mes_referencia"]

        for exp in dados["expenses"]:
            if not exp.parcela_total or exp.parcela_total <= 1:
                continue
            if not exp.parcela_atual:
                continue
            if exp.parcela_atual >= exp.parcela_total - 1:
                terminando = "este mês" if exp.parcela_atual == exp.parcela_total else "no próximo mês"
                # Calcular mes de liberacao
                if exp.parcela_atual == exp.parcela_total:
                    # ultima parcela deste mes, livre a partir do proximo
                    prox_mes = mes.month + 1 if mes.month < 12 else 1
                    prox_ano = mes.year if mes.month < 12 else mes.year + 1
                    mes_livre = date(prox_ano, prox_mes, 1)
                else:
                    # penultima parcela, livre 2 meses a frente
                    m = mes.month + 2
                    y = mes.year
                    while m > 12:
                        m -= 12
                        y += 1
                    mes_livre = date(y, m, 1)

                ref = f"{exp.nome.strip().lower()}:{exp.parcela_total}"
                alertas.append({
                    "alerta_tipo": "A3",
                    "alerta_referencia": ref,
                    "severidade": "informativo",
                    "titulo": f"{exp.nome} termina {terminando}",
                    "descricao": f"Parcela {exp.parcela_atual} de {exp.parcela_total}. R$ {float(exp.valor):,.2f}/mês livre a partir de {mes_livre.strftime('%B').lower()}.".replace(",", "X").replace(".", ",").replace("X", "."),
                    "impacto_mensal": float(exp.valor),
                    "impacto_anual": round(float(exp.valor) * 12, 2),
                    "contexto_aba": "parcelas",
                    "acao_tipo": "navegar",
                    "acao_destino": "/installments",
                })
        # Dedup por referencia (mesmo parcelamento pode ter entradas em meses diferentes)
        seen = set()
        deduped = []
        for a in alertas:
            if a["alerta_referencia"] not in seen:
                seen.add(a["alerta_referencia"])
                deduped.append(a)
        return deduped


class ScoreDeteriorandoChecker(BaseAlertChecker):
    """A4: Score caiu >=5 pontos ou subiu >=10 pontos vs mes anterior."""

    @property
    def tipo(self) -> str:
        return "A4"

    def check(self, dados: dict, config: Any) -> list[dict]:
        score_current = dados.get("score_current")
        score_previous = dados.get("score_previous")
        mes = dados["mes_referencia"]

        if not score_current or not score_previous:
            return []

        delta = score_current.score_total - score_previous.score_total
        ref = f"score:{mes.isoformat()}"

        if delta <= -5:
            # Identificar dimensao com maior queda
            dims = [
                ("comprometimento (D1)", score_current.d1_comprometimento - score_previous.d1_comprometimento),
                ("parcelas (D2)", score_current.d2_parcelas - score_previous.d2_parcelas),
                ("poupança (D3)", score_current.d3_poupanca - score_previous.d3_poupanca),
                ("comportamento (D4)", score_current.d4_comportamento - score_previous.d4_comportamento),
            ]
            pior_dim = min(dims, key=lambda d: d[1])

            return [{
                "alerta_tipo": "A4",
                "alerta_referencia": ref,
                "severidade": "atencao",
                "titulo": f"Seu score caiu {abs(delta)} pontos",
                "descricao": f"De {score_previous.score_total} para {score_current.score_total}. Principal motivo: {pior_dim[0]}.",
                "contexto_aba": "score",
                "acao_tipo": "navegar",
                "acao_destino": "/score",
            }]
        elif delta >= 10:
            return [{
                "alerta_tipo": "A4",
                "alerta_referencia": ref,
                "severidade": "informativo",
                "titulo": f"Seu score subiu {delta} pontos!",
                "descricao": f"De {score_previous.score_total} para {score_current.score_total}. Bom trabalho!",
                "contexto_aba": "score",
                "acao_tipo": "navegar",
                "acao_destino": "/score",
            }]
        return []


class ComprometimentoAltoChecker(BaseAlertChecker):
    """A5: Comprometimento com fixos acima do limiar."""

    @property
    def tipo(self) -> str:
        return "A5"

    def check(self, dados: dict, config: Any) -> list[dict]:
        renda = dados.get("total_income", 0)
        total_fixos = dados.get("total_expenses", 0)
        mes = dados["mes_referencia"]

        if renda <= 0:
            return []

        percentual = round((total_fixos / renda) * 100, 1)
        limiar = config.limiar_comprometimento

        if percentual > limiar:
            excedente = round(total_fixos - (renda * limiar / 100), 2)
            return [{
                "alerta_tipo": "A5",
                "alerta_referencia": f"comprometimento:{mes.isoformat()}",
                "severidade": "atencao",
                "titulo": f"Comprometimento com fixos acima de {limiar}%",
                "descricao": f"{percentual}% da renda comprometida (ideal: até {limiar}%). Excedente: R$ {excedente:,.2f}/mês.".replace(",", "X").replace(".", ",").replace("X", "."),
                "contexto_aba": "gastos_planejados",
                "acao_tipo": "navegar",
                "acao_destino": "/score",
            }]
        return []


class ParcelaAtivadaChecker(BaseAlertChecker):
    """A6: Parcela mudou de 0/Y para 1/Y (inicio de pagamento)."""

    @property
    def tipo(self) -> str:
        return "A6"

    def check(self, dados: dict, config: Any) -> list[dict]:
        expenses = dados["expenses"]
        prev_expenses = dados.get("prev_expenses", [])
        renda = dados.get("total_income", 0)
        total_fixos = dados.get("total_expenses", 0)
        alertas = []

        # Mapear parcelamentos do mes anterior: {(nome_lower, parcela_total): max_parcela_atual}
        prev_map: dict[tuple, int] = {}
        for exp in prev_expenses:
            if exp.parcela_total and exp.parcela_total > 1:
                key = (exp.nome.strip().lower(), exp.parcela_total)
                prev_map[key] = max(prev_map.get(key, 0), exp.parcela_atual or 0)

        # Verificar parcelamentos do mes atual com parcela_atual == 1 que nao existiam antes
        seen = set()
        for exp in expenses:
            if not exp.parcela_total or exp.parcela_total <= 1:
                continue
            if exp.parcela_atual != 1:
                continue
            key = (exp.nome.strip().lower(), exp.parcela_total)
            if key in seen:
                continue
            seen.add(key)

            prev_max = prev_map.get(key, 0)
            if prev_max == 0:
                # Nova parcela ativada
                comprometimento_str = ""
                if renda > 0:
                    pct = round((total_fixos / renda) * 100, 1)
                    comprometimento_str = f" Comprometimento subiu para {pct}%."

                alertas.append({
                    "alerta_tipo": "A6",
                    "alerta_referencia": f"{exp.nome.strip().lower()}:{exp.parcela_total}:ativada",
                    "severidade": "critico",
                    "titulo": f"{exp.nome} iniciou pagamento",
                    "descricao": f"Nova parcela de R$ {float(exp.valor):,.2f}/mês por {exp.parcela_total} meses.{comprometimento_str}".replace(",", "X").replace(".", ",").replace("X", "."),
                    "impacto_mensal": float(exp.valor),
                    "contexto_aba": "parcelas",
                    "acao_tipo": "navegar",
                    "acao_destino": "/installments",
                })
        return alertas


class AlertasIAChecker(BaseAlertChecker):
    """A7+A8: Promove alertas e gastos recorrentes disfarcados da analise IA (F06)."""

    @property
    def tipo(self) -> str:
        return "A7"

    def check(self, dados: dict, config: Any) -> list[dict]:
        analise = dados.get("analise_ia")
        if not analise:
            return []

        try:
            resultado = json.loads(analise.resultado) if isinstance(analise.resultado, str) else analise.resultado
        except (json.JSONDecodeError, TypeError):
            return []

        alertas = []

        # A7: Alertas da analise IA (max 5)
        ia_alertas = resultado.get("alertas", [])
        for i, alerta in enumerate(ia_alertas[:5]):
            sev_map = {"critico": "critico", "atencao": "atencao", "informativo": "informativo"}
            sev = sev_map.get(alerta.get("tipo", "informativo"), "informativo")
            alertas.append({
                "alerta_tipo": "A7",
                "alerta_referencia": f"ia:{i}",
                "severidade": sev,
                "titulo": alerta.get("titulo", "Alerta da análise IA"),
                "descricao": alerta.get("descricao", ""),
                "impacto_mensal": alerta.get("impacto_mensal"),
                "impacto_anual": alerta.get("impacto_anual"),
                "contexto_aba": "score",
                "acao_tipo": "navegar",
                "acao_destino": "/score",
            })

        # A8: Gastos recorrentes disfarcados
        recorrentes = resultado.get("gastos_recorrentes_disfarcados", [])
        for rec in recorrentes:
            desc = rec.get("descricao", "")
            freq = rec.get("frequencia_mensal", 0)
            valor = rec.get("valor_medio_mensal", 0)
            alertas.append({
                "alerta_tipo": "A8",
                "alerta_referencia": f"recorrente:{desc.strip().lower()}",
                "severidade": "informativo",
                "titulo": f"{desc} aparece {freq}x por mês",
                "descricao": f"Média de R$ {valor:,.2f}/mês. Considere incluir como gasto planejado para melhor controle.".replace(",", "X").replace(".", ",").replace("X", "."),
                "impacto_mensal": valor,
                "contexto_aba": "gastos_planejados",
                "acao_tipo": "criar_planejado",
            })

        return alertas


class AlertEngine:
    """Orquestra a execucao de todos os checkers e reconcilia com estado persistido."""

    def __init__(self):
        self.checkers: list[BaseAlertChecker] = [
            VencimentoProximoChecker(),
            DespesaAtrasadaChecker(),
            ParcelaEncerrandoChecker(),
            ScoreDeteriorandoChecker(),
            ComprometimentoAltoChecker(),
            ParcelaAtivadaChecker(),
            AlertasIAChecker(),
        ]

    def _checker_habilitado(self, checker: BaseAlertChecker, config: Any) -> bool:
        """Verifica se o checker esta habilitado nas configuracoes."""
        mapping = {
            "A1": config.antecedencia_vencimento > 0,
            "A2": config.alerta_atrasadas,
            "A3": config.alerta_parcelas_encerrando,
            "A4": config.alerta_score,
            "A5": config.alerta_comprometimento,
            "A6": config.alerta_parcela_ativada,
            "A7": config.alerta_ia,
            "A8": config.alerta_ia,
        }
        return mapping.get(checker.tipo, True)

    def _collect_data(self, db: Session, user_id: str, mes_referencia: date) -> dict:
        """Coleta todos os dados necessarios para os checkers."""
        today = date.today()
        prev_mes = get_previous_month(mes_referencia)

        # Expenses do mes atual (com status auto-detection)
        expenses = crud.get_expenses_by_month(db, mes_referencia, user_id)
        apply_status_auto_detection(expenses, today)

        # Expenses do mes anterior (para A6)
        prev_expenses = crud.get_expenses_by_month(db, prev_mes, user_id)

        # Totais
        total_income = crud.get_income_total_by_month(db, mes_referencia, user_id)
        total_expenses = crud.get_expense_total_by_month(db, mes_referencia, user_id)

        # Score atual e anterior (para A4)
        score_current = crud.get_score_by_month(db, user_id, mes_referencia)
        score_previous = crud.get_score_by_month(db, user_id, prev_mes)

        # Analise IA (para A7/A8)
        analise_ia = crud.get_analise_by_month(db, user_id, mes_referencia)

        return {
            "today": today,
            "mes_referencia": mes_referencia,
            "expenses": expenses,
            "prev_expenses": prev_expenses,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "score_current": score_current,
            "score_previous": score_previous,
            "analise_ia": analise_ia,
        }

    def calcular_alertas(self, db: Session, user_id: str, mes_referencia: date) -> dict:
        """Calcula todos os alertas, reconcilia com estado e retorna resultado."""
        config = crud.get_configuracao_alertas(db, user_id)
        dados = self._collect_data(db, user_id, mes_referencia)

        # Executar checkers habilitados
        alertas_brutos: list[dict] = []
        for checker in self.checkers:
            if self._checker_habilitado(checker, config):
                try:
                    resultado = checker.check(dados, config)
                    alertas_brutos.extend(resultado)
                except Exception as e:
                    logger.error("Erro no checker %s: %s", checker.tipo, e)

        # Reconciliar com estado persistido
        alertas_finais = self._reconcile(db, user_id, mes_referencia, alertas_brutos)

        # Ordenar: critico > atencao > informativo
        alertas_finais.sort(key=lambda a: (
            SEVERITY_ORDER.get(a["severidade"], 2),
            a.get("created_at") or "",
        ))

        # Montar resumo
        ativos = [a for a in alertas_finais if a["status"] in ("ativo", "visto")]
        resumo = {
            "total_ativos": len(ativos),
            "criticos": sum(1 for a in ativos if a["severidade"] == "critico"),
            "atencao": sum(1 for a in ativos if a["severidade"] == "atencao"),
            "informativos": sum(1 for a in ativos if a["severidade"] == "informativo"),
            "nao_vistos": sum(1 for a in ativos if a["status"] == "ativo"),
        }

        return {"alertas": alertas_finais, "resumo": resumo}

    def _reconcile(
        self, db: Session, user_id: str, mes_referencia: date, alertas_brutos: list[dict]
    ) -> list[dict]:
        """Reconcilia alertas gerados com estado persistido."""
        # Carregar alertas persistidos do mes
        persistidos = crud.get_alertas_by_month(db, user_id, mes_referencia)
        persistidos_map = {
            (a.alerta_tipo, a.alerta_referencia): a for a in persistidos
        }

        # Conjunto de chaves geradas neste calculo
        gerados_keys = set()
        alertas_finais = []

        for alerta_data in alertas_brutos:
            key = (alerta_data["alerta_tipo"], alerta_data["alerta_referencia"])
            gerados_keys.add(key)

            existente = persistidos_map.get(key)

            if existente:
                # Ja existe — verificar status
                if existente.status in ("dispensado", "resolvido"):
                    # Nao reaparece
                    continue

                # Atualizar dados (titulo/descricao podem mudar) e preservar status
                alerta_data["mes_referencia"] = mes_referencia
                record = crud.upsert_alerta_estado(db, user_id, alerta_data)
                alertas_finais.append(self._record_to_dict(record))
            else:
                # Novo alerta — criar com status ativo
                alerta_data["mes_referencia"] = mes_referencia
                alerta_data["status"] = "ativo"
                record = crud.upsert_alerta_estado(db, user_id, alerta_data)
                alertas_finais.append(self._record_to_dict(record))

        # Auto-resolver alertas que nao foram mais gerados
        for key, record in persistidos_map.items():
            if key not in gerados_keys and record.status in ("ativo", "visto"):
                crud.mark_alerta_resolvido(db, record)

        return alertas_finais

    def _record_to_dict(self, record) -> dict:
        """Converte AlertaEstado ORM para dict de resposta."""
        acao = None
        if record.acao_tipo:
            acao = {
                "tipo": record.acao_tipo,
                "label": self._get_action_label(record.acao_tipo),
                "referencia_id": record.acao_referencia_id,
                "destino": record.acao_destino,
            }

        return {
            "id": record.id,
            "tipo": record.alerta_tipo,
            "severidade": record.severidade,
            "titulo": record.titulo,
            "descricao": record.descricao or "",
            "impacto_mensal": float(record.impacto_mensal) if record.impacto_mensal else None,
            "impacto_anual": float(record.impacto_anual) if record.impacto_anual else None,
            "status": record.status,
            "acao": acao,
            "contexto_aba": record.contexto_aba,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }

    def _get_action_label(self, acao_tipo: str) -> str:
        """Retorna label de acao baseado no tipo."""
        labels = {
            "marcar_pago": "Marcar como pago",
            "navegar": "Ver detalhes",
            "criar_planejado": "Criar gasto planejado",
        }
        return labels.get(acao_tipo, "Ver")
