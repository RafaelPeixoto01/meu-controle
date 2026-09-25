"""
CR-056 (F07): diario de efeitos do confirm e desfazer de lote (RN-051/RN-052).

O confirm registra aqui cada coisa que gravou; o undo le o diario, compara o
estado atual de cada lancamento com o que foi gravado e decide, efeito a
efeito, entre remover, restaurar, preservar ou reportar que ja nao existe.

Por que um diario e nao os campos de auditoria da transacao: ver ADR-022.
"""
import hashlib
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app import crud
from app.models import (
    DailyExpense,
    Expense,
    ExpenseStatus,
    ImportBatch,
    ImportEffect,
    ImportTransaction,
)

TIPO_GASTO_CRIADO = "gasto_diario_criado"
TIPO_PLANEJADO_CRIADO = "planejado_criado"
TIPO_PLANEJADO_CONCILIADO = "planejado_conciliado"

ACAO_REMOVER = "remover"
ACAO_RESTAURAR = "restaurar"
ACAO_PRESERVAR = "preservar"
ACAO_JA_REMOVIDO = "ja_removido"

# Ordem de exibicao na previa: primeiro o que o undo faz, depois o que ele poupa
_ORDEM_ACAO = {ACAO_REMOVER: 0, ACAO_RESTAURAR: 1, ACAO_PRESERVAR: 2, ACAO_JA_REMOVIDO: 3}

# RF-05 alterna Pendente -> Atrasado sozinha a cada leitura do mes. Na
# assinatura os dois sao o mesmo estado; senao toda parcela futura vencida
# pareceria editada e o undo nunca a removeria.
_STATUS_EM_ABERTO = "em_aberto"
_STATUS_AUTOMATICOS = {ExpenseStatus.PENDENTE.value, ExpenseStatus.ATRASADO.value}


def _campo(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "1" if valor else "0"
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return str(valor)


def _dinheiro(valor) -> str:
    # float() iguala o Decimal lido do banco ao float atribuido no confirm
    return f"{float(valor):.2f}"


def entity_signature(entidade: DailyExpense | Expense) -> str:
    """
    Hash do estado de um lancamento nos campos que o usuario (ou outro lote)
    pode alterar. Igual ao do diario = ninguem mexeu desde o confirm.
    """
    if isinstance(entidade, DailyExpense):
        partes = [
            "gasto",
            _campo(entidade.mes_referencia),
            _campo(entidade.descricao),
            _dinheiro(entidade.valor),
            _campo(entidade.data),
            _campo(entidade.categoria),
            _campo(entidade.subcategoria),
            _campo(entidade.metodo_pagamento),
        ]
    elif isinstance(entidade, Expense):
        status = entidade.status
        if status in _STATUS_AUTOMATICOS:
            status = _STATUS_EM_ABERTO
        partes = [
            "planejado",
            _campo(entidade.mes_referencia),
            _campo(entidade.nome),
            _dinheiro(entidade.valor),
            _campo(entidade.vencimento),
            _campo(entidade.categoria),
            _campo(entidade.subcategoria),
            _campo(entidade.parcela_atual),
            _campo(entidade.parcela_total),
            _campo(entidade.recorrente),
            status,
        ]
    else:
        raise TypeError(f"Lançamento sem assinatura: {type(entidade).__name__}")
    return hashlib.sha256("|".join(partes).encode("utf-8")).hexdigest()


# ========== Registro (no confirm) ==========

@dataclass
class _Pendente:
    tx_id: str
    tipo: str
    entidade: DailyExpense | Expense
    status_anterior: str | None = None
    valor_anterior: float | None = None


class EffectJournal:
    """
    Acumula os efeitos de um confirm e os grava no fim, de uma vez.

    Adiar a gravacao nao e detalhe: a assinatura precisa ser a do estado FINAL
    do confirm, e o id das despesas criadas so existe depois do flush. Um
    lancamento tocado duas vezes no mesmo confirm (ex.: conciliado por uma
    linha e reconciliado pela RN-046 de outra) fica com o PRIMEIRO efeito — e o
    que guarda o estado de antes do lote, que e o que o undo precisa devolver.
    """

    def __init__(self, batch: ImportBatch):
        self._batch = batch
        # Chave pela identidade do objeto: despesas recem-criadas ainda nao tem id
        self._por_entidade: dict[int, _Pendente] = {}

    def _registrar(self, pendente: _Pendente) -> None:
        self._por_entidade.setdefault(id(pendente.entidade), pendente)

    def criado(self, tx: ImportTransaction, entidade: DailyExpense | Expense) -> None:
        tipo = TIPO_GASTO_CRIADO if isinstance(entidade, DailyExpense) else TIPO_PLANEJADO_CRIADO
        self._registrar(_Pendente(tx.id, tipo, entidade))

    def conciliado(
        self,
        tx: ImportTransaction,
        entidade: Expense,
        status_anterior: str,
        valor_anterior: float,
    ) -> None:
        self._registrar(
            _Pendente(tx.id, TIPO_PLANEJADO_CONCILIADO, entidade, status_anterior, valor_anterior)
        )

    def gravar(self, db: Session) -> int:
        """Grava o diario. Chamar depois da ultima alteracao do confirm."""
        db.flush()  # ids das despesas criadas
        for p in self._por_entidade.values():
            db.add(ImportEffect(
                batch_id=self._batch.id,
                transaction_id=p.tx_id,
                user_id=self._batch.user_id,
                tipo=p.tipo,
                entidade_id=p.entidade.id,
                assinatura=entity_signature(p.entidade),
                status_anterior=p.status_anterior,
                valor_anterior=p.valor_anterior,
            ))
        return len(self._por_entidade)


# ========== Desfazer ==========

def undo_blocker(batch: ImportBatch) -> str | None:
    """Motivo pelo qual o lote nao pode ser desfeito, ou None se pode."""
    if batch.status != "confirmado":
        return "Só é possível desfazer uma importação confirmada"
    if batch.confirmado_em is None:
        # Sem diario, o undo cairia nos furos que motivaram o CR-056: apagaria a
        # parcela pre-existente conciliada pela RN-046 e deixaria as futuras
        return (
            "Esta importação foi confirmada antes do recurso de desfazer existir "
            "e não pode ser desfeita"
        )
    return None


def undo_blocker_dependencies(db: Session, batch: ImportBatch) -> str | None:
    """
    Undo em ordem inversa entre lotes dependentes (RN-051).

    Se o lote B, confirmado depois, conciliou uma parcela que A criou,
    desfazer A primeiro manteria a parcela (alterada depois) e apagaria o resto
    da serie; desfazer B em seguida a devolveria a Pendente — orfa, sem lote
    que ainda a possa remover. Na ordem B → A, o undo de B devolve a parcela
    exatamente ao estado que A gravou, e o de A a remove.

    Alteracao manual (fora de um lote) continua sendo so preservada: nao ha
    ordem a respeitar.
    """
    posterior = crud.get_later_batch_touching(db, batch)
    if posterior is None:
        return None
    return (
        f"Desfaça antes a importação \"{posterior.filename}\", confirmada depois "
        "desta e que alterou lançamentos criados ou conciliados por ela"
    )


@dataclass
class UndoStep:
    efeito: ImportEffect
    acao: str
    entidade: DailyExpense | Expense | None
    tx: ImportTransaction | None


def plan_undo(db: Session, batch: ImportBatch) -> list[UndoStep]:
    """
    Decide o destino de cada efeito do lote a partir do estado atual. Nao
    altera nada — a previa e a execucao usam o mesmo plano.
    """
    efeitos = list(batch.efeitos)
    ids_gastos = [e.entidade_id for e in efeitos if e.tipo == TIPO_GASTO_CRIADO]
    ids_planejados = [e.entidade_id for e in efeitos if e.tipo != TIPO_GASTO_CRIADO]
    # Sempre filtrado pelo dono do lote: o diario nunca alcanca dado alheio
    gastos = crud.get_daily_expenses_by_ids(db, ids_gastos, batch.user_id)
    planejados = crud.get_expenses_by_ids(db, ids_planejados, batch.user_id)
    tx_por_id = {t.id: t for t in batch.transacoes}

    passos = []
    for efeito in efeitos:
        mapa = gastos if efeito.tipo == TIPO_GASTO_CRIADO else planejados
        entidade = mapa.get(efeito.entidade_id)
        if entidade is None:
            acao = ACAO_JA_REMOVIDO
        elif entity_signature(entidade) != efeito.assinatura:
            acao = ACAO_PRESERVAR
        elif efeito.tipo == TIPO_PLANEJADO_CONCILIADO:
            acao = ACAO_RESTAURAR
        else:
            acao = ACAO_REMOVER
        passos.append(UndoStep(efeito, acao, entidade, tx_por_id.get(efeito.transaction_id)))
    return passos


def summarize(passos: list[UndoStep]) -> dict[str, int]:
    def conta(acao: str, tipo: str | None = None) -> int:
        return sum(
            1 for p in passos
            if p.acao == acao and (tipo is None or p.efeito.tipo == tipo)
        )

    return {
        "gastos_diarios_removidos": conta(ACAO_REMOVER, TIPO_GASTO_CRIADO),
        "planejados_removidos": conta(ACAO_REMOVER, TIPO_PLANEJADO_CRIADO),
        "planejados_restaurados": conta(ACAO_RESTAURAR),
        "preservados": conta(ACAO_PRESERVAR),
        "ja_removidos": conta(ACAO_JA_REMOVIDO),
    }


def describe(passos: list[UndoStep]) -> list[dict]:
    """Itens da previa, no formato de `schemas.ImportUndoItem`."""
    itens = []
    for p in passos:
        efeito, ent, tx = p.efeito, p.entidade, p.tx
        item = {
            "entidade": "gasto_diario" if efeito.tipo == TIPO_GASTO_CRIADO else "planejado",
            "efeito": "conciliado" if efeito.tipo == TIPO_PLANEJADO_CONCILIADO else "criado",
            "acao": p.acao,
            "parcela_atual": None,
            "parcela_total": None,
            "status_anterior": efeito.status_anterior,
            "valor_anterior": (
                float(efeito.valor_anterior) if efeito.valor_anterior is not None else None
            ),
        }
        if isinstance(ent, DailyExpense):
            item.update(descricao=ent.descricao, valor=float(ent.valor), data=ent.data)
        elif isinstance(ent, Expense):
            item.update(
                descricao=ent.nome,
                valor=float(ent.valor),
                data=ent.vencimento,
                parcela_atual=ent.parcela_atual,
                parcela_total=ent.parcela_total,
            )
        else:
            # Ja removido: so resta o que veio do documento
            item.update(
                descricao=tx.descricao if tx else "",
                valor=float(tx.valor) if tx else 0.0,
                data=tx.data if tx else None,
            )
        itens.append(item)

    itens.sort(key=lambda i: (_ORDEM_ACAO[i["acao"]], i["data"] or date.min, i["descricao"]))
    return itens


def apply_undo(db: Session, batch: ImportBatch, passos: list[UndoStep]) -> dict[str, int]:
    """
    Executa o plano. NAO faz commit — o router controla a transacao, para o
    undo ser tudo ou nada.
    """
    for p in passos:
        if p.acao == ACAO_REMOVER:
            db.delete(p.entidade)
        elif p.acao == ACAO_RESTAURAR:
            p.entidade.status = p.efeito.status_anterior
            p.entidade.valor = p.efeito.valor_anterior

    # RN-052: transacao volta a ser importavel so se NADA dela ficou gravado.
    # Com um lancamento preservado, 'confirmada' e o que mantem a dedup (RN-042)
    # protegendo contra lancar de novo o que o usuario decidiu manter.
    com_preservado = {p.efeito.transaction_id for p in passos if p.acao == ACAO_PRESERVAR}
    for tx in batch.transacoes:
        if tx.status == "confirmada" and tx.id not in com_preservado:
            tx.status = "revertida"

    batch.status = "revertido"
    batch.revertido_em = datetime.now()
    return summarize(passos)
