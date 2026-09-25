"""
CR-056 (F07): historico de importacoes, diario de efeitos do confirm e
desfazer de lote (RN-051/RN-052). API Anthropic sempre mockada.
"""
from datetime import date, datetime, timedelta

from app.models import (
    DailyExpense,
    Expense,
    ExpenseStatus,
    ImportBatch,
    ImportCategoryRule,
    ImportEffect,
    ImportTransaction,
)
from app import import_undo
from app.import_undo import entity_signature

# Fixtures e helpers compartilhados com a suite da F07 (pytest registra as
# fixtures importadas no namespace do modulo)
from tests.test_imports import (  # noqa: F401
    TX_IGNORAR,
    TX_MATCH_LUZ,
    TX_PADARIA,
    TX_PARCELAMENTO,
    client,
    db,
    engine,
    open_expense,
    session_factory,
    upload_batch,
    user_a,
    user_b,
)


# ========== Helpers ==========

def tx_id_por_descricao(batch, descricao):
    return next(t["id"] for t in batch["transacoes"] if t["descricao"] == descricao)


def decisao_gasto(tx_id, **campos):
    decisao = {
        "id": tx_id,
        "acao": "criar_gasto_diario",
        "descricao": "Padaria Stella",
        "valor": 23.50,
        "data": "2026-07-28",
        "categoria": "Alimentação",
        "subcategoria": "Padaria",
        "metodo_pagamento": "Cartão de Crédito",
    }
    decisao.update(campos)
    return decisao


def decisao_parcelado(tx_id, **campos):
    decisao = {
        "id": tx_id,
        "acao": "criar_planejado_parcelado",
        "descricao": "Netshoes",
        "parcela_atual": 3,
        "parcela_total": 10,
    }
    decisao.update(campos)
    return decisao


def confirmar(client, batch, decisoes):
    r = client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": decisoes})
    assert r.status_code == 200, r.text
    return r.json()


def lote_completo(client):
    """
    Lote com as tres acoes: gasto diario, conciliacao do planejado de luz e
    serie de parcelas. Precisa da fixture `open_expense` para a conciliacao.
    """
    batch = upload_batch(client, transacoes=[TX_PADARIA, TX_MATCH_LUZ, TX_PARCELAMENTO])
    confirmar(client, batch, [
        decisao_gasto(tx_id_por_descricao(batch, "PADARIA STELLA")),
        {
            "id": tx_id_por_descricao(batch, "CEMIG ENERGIA"),
            "acao": "atualizar_planejado",
            "expense_id": "expense-luz",
            "valor": 187.32,
        },
        decisao_parcelado(tx_id_por_descricao(batch, "Netshoes")),
    ])
    return batch


def lote_so_gasto(client):
    batch = upload_batch(client, transacoes=[TX_PADARIA])
    confirmar(client, batch, [decisao_gasto(batch["transacoes"][0]["id"])])
    return batch


def desfazer(client, batch_id, esperado=200):
    r = client.post(f"/api/imports/{batch_id}/undo")
    assert r.status_code == esperado, r.text
    return r.json()


def previa(client, batch_id, esperado=200):
    r = client.get(f"/api/imports/{batch_id}/undo-preview")
    assert r.status_code == esperado, r.text
    return r.json()


def parcela_netshoes(db, numero):
    return db.query(Expense).filter(
        Expense.nome == "Netshoes", Expense.parcela_atual == numero
    ).one()


def netshoes_existente(db, user_a, parcela, status=ExpenseStatus.PENDENTE.value, valor=149.90):
    """Parcela ja cadastrada — compra em 15/07: a parcela k vence em 07+(k-1)."""
    expense = Expense(
        user_id=user_a.id,
        mes_referencia=date(2026, 6 + parcela, 1),
        nome="Netshoes",
        valor=valor,
        vencimento=date(2026, 6 + parcela, 15),
        parcela_atual=parcela,
        parcela_total=10,
        recorrente=False,
        status=status,
    )
    db.add(expense)
    db.commit()
    return expense


# ========== Assinatura ==========

class TestEntitySignature:
    def _expense(self, **campos):
        base = dict(
            id="e1", user_id="u", mes_referencia=date(2026, 9, 1), nome="Netshoes",
            valor=149.90, vencimento=date(2026, 9, 15), parcela_atual=3,
            parcela_total=10, recorrente=False, status=ExpenseStatus.PENDENTE.value,
        )
        base.update(campos)
        return Expense(**base)

    def test_pendente_e_atrasado_sao_o_mesmo_estado(self):
        """RF-05 alterna os dois sozinha — nao e edicao do usuario."""
        assert entity_signature(self._expense(status="Pendente")) == entity_signature(
            self._expense(status="Atrasado")
        )

    def test_pago_difere_de_em_aberto(self):
        assert entity_signature(self._expense(status="Pago")) != entity_signature(
            self._expense(status="Pendente")
        )

    def test_valor_decimal_do_banco_iguala_float_do_confirm(self):
        from decimal import Decimal
        assert entity_signature(self._expense(valor=Decimal("149.90"))) == entity_signature(
            self._expense(valor=149.9)
        )

    def test_qualquer_campo_editavel_muda_a_assinatura(self):
        base = entity_signature(self._expense())
        for campo, valor in [
            ("nome", "Outra"), ("valor", 150.0), ("vencimento", date(2026, 9, 16)),
            ("categoria", "Casa"), ("parcela_total", 11), ("recorrente", True),
        ]:
            assert entity_signature(self._expense(**{campo: valor})) != base, campo

    def test_gasto_diario_editado_muda_a_assinatura(self):
        def gasto(**campos):
            base = dict(
                id="d1", user_id="u", mes_referencia=date(2026, 7, 1),
                descricao="Padaria", valor=23.5, data=date(2026, 7, 28),
                categoria="Alimentação", subcategoria="Padaria", metodo_pagamento="Pix",
            )
            base.update(campos)
            return DailyExpense(**base)

        assert entity_signature(gasto()) == entity_signature(gasto())
        assert entity_signature(gasto(metodo_pagamento="Dinheiro")) != entity_signature(gasto())


# ========== Diario do confirm ==========

class TestDiarioDoConfirm:
    def test_grava_um_efeito_por_lancamento(self, client, db, open_expense):
        batch = lote_completo(client)

        efeitos = db.query(ImportEffect).filter(ImportEffect.batch_id == batch["id"]).all()
        por_tipo = {}
        for e in efeitos:
            por_tipo.setdefault(e.tipo, []).append(e)

        assert len(por_tipo["gasto_diario_criado"]) == 1
        # a serie inteira, nao so a ancora: parcelas 3..10
        assert len(por_tipo["planejado_criado"]) == 8
        conciliado = por_tipo["planejado_conciliado"]
        assert len(conciliado) == 1
        assert conciliado[0].entidade_id == "expense-luz"
        assert conciliado[0].status_anterior == ExpenseStatus.PENDENTE.value
        assert float(conciliado[0].valor_anterior) == 200.00

    def test_confirm_marca_o_lote_como_desfazivel(self, client, db, open_expense):
        batch = lote_completo(client)
        lote = db.get(ImportBatch, batch["id"])
        assert lote.confirmado_em is not None

    def test_parcela_pre_existente_e_registrada_como_conciliada(self, client, db, user_a):
        """RN-046: a ancora ja existia — o diario nao pode chama-la de criada."""
        existente = netshoes_existente(db, user_a, parcela=3)
        batch = upload_batch(client, transacoes=[TX_PARCELAMENTO])
        confirmar(client, batch, [decisao_parcelado(batch["transacoes"][0]["id"])])

        efeitos = db.query(ImportEffect).all()
        da_existente = [e for e in efeitos if e.entidade_id == existente.id]
        assert [e.tipo for e in da_existente] == ["planejado_conciliado"]
        assert da_existente[0].status_anterior == ExpenseStatus.PENDENTE.value
        assert sum(e.tipo == "planejado_criado" for e in efeitos) == 7  # 4..10

    def test_descartadas_nao_geram_efeito(self, client, db):
        batch = upload_batch(client, transacoes=[TX_PADARIA, TX_IGNORAR])
        confirmar(client, batch, [decisao_gasto(tx_id_por_descricao(batch, "PADARIA STELLA"))])
        assert db.query(ImportEffect).count() == 1


# ========== Historico ==========

class TestHistorico:
    def test_lista_os_lotes_com_contadores(self, client, db):
        confirmado = lote_so_gasto(client)
        pendente = upload_batch(client, transacoes=[TX_PADARIA, TX_IGNORAR])

        r = client.get("/api/imports")
        assert r.status_code == 200
        corpo = r.json()
        assert corpo["total"] == 2
        ids = [i["id"] for i in corpo["items"]]
        assert set(ids) == {confirmado["id"], pendente["id"]}

        por_id = {i["id"]: i for i in corpo["items"]}
        c = por_id[confirmado["id"]]
        assert c["status"] == "confirmado"
        assert c["confirmadas"] == 1
        assert c["total_transacoes"] == 1
        assert c["pode_desfazer"] is True
        assert c["confirmado_em"] is not None

        p = por_id[pendente["id"]]
        assert p["status"] == "pendente_revisao"
        assert p["total_transacoes"] == 2
        assert p["pode_desfazer"] is False

    def test_mais_recentes_primeiro_e_paginado(self, client, db):
        lotes = [lote_so_gasto(client) for _ in range(3)]
        # created_at explicito: tres uploads no mesmo segundo nao ordenam sozinhos
        base = datetime(2026, 9, 1, 10, 0, 0)
        for i, lote in enumerate(lotes):
            db.get(ImportBatch, lote["id"]).created_at = base + timedelta(minutes=i)
        db.commit()

        p1 = client.get("/api/imports", params={"page": 1, "page_size": 2}).json()
        p2 = client.get("/api/imports", params={"page": 2, "page_size": 2}).json()

        assert p1["total"] == 3 and p1["page_size"] == 2
        assert [i["id"] for i in p1["items"]] == [lotes[2]["id"], lotes[1]["id"]]
        assert [i["id"] for i in p2["items"]] == [lotes[0]["id"]]

    def test_parametros_de_paginacao_invalidos(self, client):
        for params in ({"page": 0}, {"page_size": 0}, {"page_size": 51}):
            assert client.get("/api/imports", params=params).status_code == 422, params

    def test_lote_de_outro_usuario_nao_aparece(self, client, db, user_b):
        db.add(ImportBatch(
            user_id=user_b.id, filename="alheio.pdf", status="confirmado",
            modelo="x", confirmado_em=datetime.now(),
        ))
        db.commit()
        lote_so_gasto(client)

        corpo = client.get("/api/imports").json()
        assert corpo["total"] == 1
        assert all(i["filename"] != "alheio.pdf" for i in corpo["items"])

    def test_lote_confirmado_antes_do_cr_nao_pode_ser_desfeito(self, client, db):
        batch = lote_so_gasto(client)
        db.get(ImportBatch, batch["id"]).confirmado_em = None  # historico legado
        db.commit()

        item = client.get("/api/imports").json()["items"][0]
        assert item["status"] == "confirmado"
        assert item["pode_desfazer"] is False

    def test_lote_orfao_em_processando_aparece_como_erro(self, client, db, user_a):
        """RN-048 tambem no historico."""
        db.add(ImportBatch(
            user_id=user_a.id, filename="orfao.pdf", status="processando", modelo="x",
            created_at=datetime.now() - timedelta(hours=2),
        ))
        db.commit()

        item = client.get("/api/imports").json()["items"][0]
        assert item["status"] == "erro"


# ========== Desfazer ==========

class TestDesfazer:
    def test_desfaz_o_lote_inteiro(self, client, db, open_expense):
        batch = lote_completo(client)

        r = desfazer(client, batch["id"])
        assert r == {
            "gastos_diarios_removidos": 1,
            "planejados_removidos": 8,
            "planejados_restaurados": 1,
            "preservados": 0,
            "ja_removidos": 0,
        }

        db.expire_all()
        assert db.query(DailyExpense).count() == 0
        assert db.query(Expense).filter(Expense.nome == "Netshoes").count() == 0
        luz = db.get(Expense, "expense-luz")
        assert luz.status == ExpenseStatus.PENDENTE.value
        assert float(luz.valor) == 200.00

        lote = db.get(ImportBatch, batch["id"])
        assert lote.status == "revertido"
        assert lote.revertido_em is not None
        assert {t.status for t in lote.transacoes} == {"revertida"}

    def test_previa_nao_altera_nada_e_bate_com_o_undo(self, client, db, open_expense):
        batch = lote_completo(client)

        p = previa(client, batch["id"])
        db.expire_all()
        assert db.query(DailyExpense).count() == 1
        assert db.get(ImportBatch, batch["id"]).status == "confirmado"

        acoes = [i["acao"] for i in p["itens"]]
        assert acoes.count("remover") == 9 and acoes.count("restaurar") == 1
        luz = next(i for i in p["itens"] if i["acao"] == "restaurar")
        assert luz["status_anterior"] == "Pendente" and luz["valor_anterior"] == 200.0

        r = desfazer(client, batch["id"])
        assert {k: p[k] for k in r} == r

    def test_gasto_editado_depois_e_preservado(self, client, db):
        batch = lote_so_gasto(client)
        gasto = db.query(DailyExpense).one()
        gasto.valor = 30.00  # o usuario corrigiu o valor
        db.commit()

        assert previa(client, batch["id"])["itens"][0]["acao"] == "preservar"
        r = desfazer(client, batch["id"])
        assert r["preservados"] == 1 and r["gastos_diarios_removidos"] == 0

        db.expire_all()
        assert db.query(DailyExpense).count() == 1
        # RN-052: a transacao do lancamento mantido continua 'confirmada'
        assert db.query(ImportTransaction).one().status == "confirmada"

    def test_gasto_ja_apagado_e_reportado(self, client, db):
        batch = lote_so_gasto(client)
        db.delete(db.query(DailyExpense).one())
        db.commit()

        item = previa(client, batch["id"])["itens"][0]
        assert item["acao"] == "ja_removido"
        assert item["descricao"] == "PADARIA STELLA"  # vem da transacao
        r = desfazer(client, batch["id"])
        assert r["ja_removidos"] == 1
        db.expire_all()
        assert db.query(ImportTransaction).one().status == "revertida"

    def test_parcela_que_so_ficou_atrasada_e_removida(self, client, db):
        """RF-05 nao conta como edicao."""
        batch = upload_batch(client, transacoes=[TX_PARCELAMENTO])
        confirmar(client, batch, [decisao_parcelado(batch["transacoes"][0]["id"])])
        parcela_netshoes(db, 4).status = ExpenseStatus.ATRASADO.value
        db.commit()

        r = desfazer(client, batch["id"])
        assert r["planejados_removidos"] == 8 and r["preservados"] == 0

    def test_parcela_futura_paga_a_mao_e_preservada(self, client, db):
        batch = upload_batch(client, transacoes=[TX_PARCELAMENTO])
        confirmar(client, batch, [decisao_parcelado(batch["transacoes"][0]["id"])])
        parcela_netshoes(db, 5).status = ExpenseStatus.PAGO.value
        db.commit()

        r = desfazer(client, batch["id"])
        assert r["planejados_removidos"] == 7 and r["preservados"] == 1
        db.expire_all()
        restantes = db.query(Expense).filter(Expense.nome == "Netshoes").all()
        assert [e.parcela_atual for e in restantes] == [5]

    def test_parcela_pre_existente_e_restaurada_e_nunca_apagada(self, client, db, user_a):
        """O furo que motivou o diario: RN-046 grava a existente em expense_id_criado."""
        existente = netshoes_existente(db, user_a, parcela=3, valor=150.00)
        existente_id = existente.id
        batch = upload_batch(client, transacoes=[TX_PARCELAMENTO])
        confirmar(client, batch, [decisao_parcelado(batch["transacoes"][0]["id"])])

        lote = db.get(ImportBatch, batch["id"])
        assert lote.transacoes[0].expense_id_criado == existente_id  # o furo

        r = desfazer(client, batch["id"])
        assert r["planejados_restaurados"] == 1 and r["planejados_removidos"] == 7

        db.expire_all()
        parcela = db.get(Expense, existente_id)
        assert parcela is not None
        assert parcela.status == ExpenseStatus.PENDENTE.value
        assert float(parcela.valor) == 150.00

    def test_conciliado_editado_depois_nao_e_restaurado(self, client, db, open_expense):
        batch = upload_batch(client, transacoes=[TX_MATCH_LUZ])
        confirmar(client, batch, [{
            "id": batch["transacoes"][0]["id"], "acao": "atualizar_planejado",
            "expense_id": "expense-luz", "valor": 187.32,
        }])
        luz = db.get(Expense, "expense-luz")
        db.refresh(luz)
        luz.valor = 190.00
        db.commit()

        r = desfazer(client, batch["id"])
        assert r["preservados"] == 1 and r["planejados_restaurados"] == 0
        db.expire_all()
        assert db.get(Expense, "expense-luz").status == ExpenseStatus.PAGO.value

    def test_lancamento_tocado_duas_vezes_no_lote_volta_ao_estado_original(
        self, client, db, user_a
    ):
        """
        Uma linha concilia a parcela 3 e outra a reconcilia pela RN-046 no mesmo
        confirm: o undo precisa devolver o estado de ANTES do lote.
        """
        existente = netshoes_existente(db, user_a, parcela=3, valor=150.00)
        existente_id = existente.id
        conciliacao = {**TX_MATCH_LUZ, "descricao": "NETSHOES 03/10", "expense_id": existente_id}
        batch = upload_batch(client, transacoes=[conciliacao, TX_PARCELAMENTO])
        confirmar(client, batch, [
            {"id": tx_id_por_descricao(batch, "NETSHOES 03/10"), "acao": "atualizar_planejado",
             "expense_id": existente_id, "valor": 149.90},
            decisao_parcelado(tx_id_por_descricao(batch, "Netshoes"), valor=149.95),
        ])

        desfazer(client, batch["id"])
        db.expire_all()
        parcela = db.get(Expense, existente_id)
        assert parcela.status == ExpenseStatus.PENDENTE.value
        assert float(parcela.valor) == 150.00

    def test_parcela_conciliada_por_outro_lote_e_preservada(self, client, db):
        """O lote B mexeu no que o lote A criou: desfazer A nao pode apagar."""
        lote_a = upload_batch(client, transacoes=[TX_PARCELAMENTO])
        confirmar(client, lote_a, [decisao_parcelado(lote_a["transacoes"][0]["id"])])
        parcela_4 = parcela_netshoes(db, 4)
        parcela_4.status = ExpenseStatus.PAGO.value  # efeito do lote B
        db.commit()

        r = desfazer(client, lote_a["id"])
        assert r["preservados"] == 1
        db.expire_all()
        assert db.get(Expense, parcela_4.id) is not None

    def test_reimportar_depois_do_undo_nao_marca_duplicada(self, client, db):
        batch = lote_so_gasto(client)
        desfazer(client, batch["id"])

        novo = upload_batch(client, transacoes=[TX_PADARIA])
        assert novo["transacoes"][0]["status"] == "pendente"

    def test_lancamento_preservado_continua_protegido_pela_dedup(self, client, db):
        batch = lote_so_gasto(client)
        db.query(DailyExpense).one().valor = 30.00
        db.commit()
        desfazer(client, batch["id"])

        novo = upload_batch(client, transacoes=[TX_PADARIA])
        assert novo["transacoes"][0]["status"] == "duplicada"

    def test_regras_aprendidas_permanecem(self, client, db):
        batch = upload_batch(client, transacoes=[TX_PADARIA])
        confirmar(client, batch, [decisao_gasto(batch["transacoes"][0]["id"], metodo_pagamento="Pix")])
        assert db.query(ImportCategoryRule).count() == 1

        desfazer(client, batch["id"])
        db.expire_all()
        assert db.query(ImportCategoryRule).count() == 1

    def test_lote_revertido_pode_ser_reimportado_e_desfeito_de_novo(self, client, db):
        primeiro = lote_so_gasto(client)
        desfazer(client, primeiro["id"])
        segundo = lote_so_gasto(client)

        r = desfazer(client, segundo["id"])
        assert r["gastos_diarios_removidos"] == 1


class TestDesfazerRecusado:
    def test_lote_pendente_retorna_409(self, client):
        batch = upload_batch(client, transacoes=[TX_PADARIA])
        desfazer(client, batch["id"], esperado=409)
        previa(client, batch["id"], esperado=409)

    def test_lote_ja_revertido_retorna_409(self, client):
        batch = lote_so_gasto(client)
        desfazer(client, batch["id"])
        desfazer(client, batch["id"], esperado=409)

    def test_lote_sem_diario_retorna_409(self, client, db):
        batch = lote_so_gasto(client)
        db.get(ImportBatch, batch["id"]).confirmado_em = None
        db.commit()

        r = client.post(f"/api/imports/{batch['id']}/undo")
        assert r.status_code == 409
        assert "antes do recurso de desfazer" in r.json()["detail"]
        db.expire_all()
        assert db.query(DailyExpense).count() == 1

    def test_lote_de_outro_usuario_retorna_404(self, client, db, user_b):
        alheio = ImportBatch(
            user_id=user_b.id, filename="alheio.pdf", status="confirmado",
            modelo="x", confirmado_em=datetime.now(),
        )
        db.add(alheio)
        db.commit()

        desfazer(client, alheio.id, esperado=404)
        previa(client, alheio.id, esperado=404)

    def test_descartar_lote_revertido_retorna_409(self, client):
        batch = lote_so_gasto(client)
        desfazer(client, batch["id"])
        assert client.delete(f"/api/imports/{batch['id']}").status_code == 409


class TestDiarioNaoAlcancaOutroUsuario:
    def test_efeito_apontando_para_lancamento_alheio_e_tratado_como_ausente(
        self, client, db, user_b
    ):
        """Defesa em profundidade: o plano sempre filtra pelo dono do lote."""
        batch = lote_so_gasto(client)
        alheio = DailyExpense(
            user_id=user_b.id, mes_referencia=date(2026, 7, 1), descricao="Alheio",
            valor=10, data=date(2026, 7, 1), categoria="Alimentação",
            subcategoria="Padaria", metodo_pagamento="Pix",
        )
        db.add(alheio)
        db.flush()
        efeito = db.query(ImportEffect).one()
        efeito.entidade_id = alheio.id
        efeito.assinatura = entity_signature(alheio)
        db.commit()

        r = desfazer(client, batch["id"])
        assert r["ja_removidos"] == 1
        db.expire_all()
        assert db.get(DailyExpense, alheio.id) is not None


class TestPlanoPuro:
    def test_summarize_conta_por_acao_e_tipo(self):
        def passo(tipo, acao):
            return import_undo.UndoStep(ImportEffect(tipo=tipo), acao, None, None)

        passos = [
            passo("gasto_diario_criado", "remover"),
            passo("planejado_criado", "remover"),
            passo("planejado_criado", "remover"),
            passo("planejado_conciliado", "restaurar"),
            passo("planejado_criado", "preservar"),
            passo("gasto_diario_criado", "ja_removido"),
        ]
        assert import_undo.summarize(passos) == {
            "gastos_diarios_removidos": 1,
            "planejados_removidos": 2,
            "planejados_restaurados": 1,
            "preservados": 1,
            "ja_removidos": 1,
        }
