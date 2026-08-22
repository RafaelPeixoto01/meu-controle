"""
CR-046 (F07): Testes da importacao de extratos/faturas em PDF via IA.
API Anthropic sempre mockada (call_import_api).
"""
import json
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db, get_session_factory
from app.auth import get_current_user
from app.rate_limit import limiter
from app.models import (
    DailyExpense,
    Expense,
    ExpenseStatus,
    ImportBatch,
    ImportTransaction,
    User,
)
from app.ai_analysis import DEFAULT_MODEL, AiRefusalError
from app.import_service import (
    STALE_PROCESSING_MINUTES,
    call_import_api,
    compute_fingerprint,
    normalize_description,
    validate_ai_result,
)


PDF_BYTES = b"%PDF-1.4 conteudo fake de teste para upload"


# ========== Fixtures ==========

@pytest.fixture
def engine():
    # StaticPool: todas as sessoes compartilham a mesma conexao in-memory
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def user_a(db):
    user = User(id="user-a", nome="User A", email="a@example.com", password_hash="x")
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def user_b(db):
    user = User(id="user-b", nome="User B", email="b@example.com", password_hash="x")
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def open_expense(db, user_a):
    """Gasto planejado Pendente do mes corrente (candidato a match)."""
    hoje = date.today()
    expense = Expense(
        id="expense-luz",
        user_id=user_a.id,
        mes_referencia=date(hoje.year, hoje.month, 1),
        nome="Energia elétrica",
        valor=200.00,
        vencimento=date(hoje.year, hoje.month, 15),
        recorrente=True,
        status=ExpenseStatus.PENDENTE.value,
    )
    db.add(expense)
    db.commit()
    return expense


@pytest.fixture
def client(session_factory, user_a, monkeypatch):
    """TestClient autenticado como user_a, com DB in-memory e API key fake."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("IMPORT_ENABLED", raising=False)
    limiter.reset()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # CR-052: a BackgroundTasks abre a propria sessao; sem este override ela
    # falaria com o banco real em vez do in-memory do teste
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_current_user] = lambda: user_a
    yield TestClient(app)
    app.dependency_overrides.clear()


def ai_result(transacoes, banco="Nubank", tipo_documento="fatura"):
    return {
        "resultado": {
            "banco": banco,
            "tipo_documento": tipo_documento,
            "transacoes": transacoes,
        },
        "tokens_input": 1000,
        "tokens_output": 500,
        "modelo": "claude-test",
        "tempo_processamento_ms": 1234,
    }


TX_PADARIA = {
    "data": "2026-07-28",
    "descricao": "PADARIA STELLA",
    "valor": 23.50,
    "classificacao": "gasto_diario",
    "categoria": "Alimentação",
    "subcategoria": "Padaria",
    "metodo_pagamento": "Cartão de Crédito",
    "expense_id": None,
    "motivo_ignorar": None,
}

TX_MATCH_LUZ = {
    "data": "2026-07-10",
    "descricao": "CEMIG ENERGIA",
    "valor": 187.32,
    "classificacao": "match_planejado",
    "expense_id": "expense-luz",
    "categoria": None,
    "subcategoria": None,
    "metodo_pagamento": None,
    "motivo_ignorar": None,
}

TX_PARCELAMENTO = {
    "data": "2026-07-15",
    "descricao": "Netshoes",
    "valor": 149.90,
    "classificacao": "parcelamento",
    "categoria": "Compras Pessoais",
    "subcategoria": "Roupas",
    "metodo_pagamento": "Cartão de Crédito",
    "expense_id": None,
    "motivo_ignorar": None,
    "parcela_atual": 3,
    "parcela_total": 10,
}

TX_IGNORAR = {
    "data": "2026-07-05",
    "descricao": "PAGAMENTO RECEBIDO",
    "valor": 2500.00,
    "classificacao": "ignorar",
    "motivo_ignorar": "pagamento de fatura",
}


def upload(client, transacoes=None, **kwargs):
    """
    POST cru do upload. CR-052: responde 202 com o lote ainda em 'processando'
    — o TestClient roda a BackgroundTasks antes de devolver o controle, entao
    o lote ja esta pronto no banco quando esta funcao retorna.
    """
    if transacoes is None:
        transacoes = [TX_PADARIA, TX_MATCH_LUZ, TX_IGNORAR]
    result = ai_result(transacoes, **kwargs)
    with patch("app.import_service.call_import_api", return_value=result):
        return client.post(
            "/api/imports",
            files={"file": ("fatura.pdf", PDF_BYTES, "application/pdf")},
        )


def upload_batch(client, transacoes=None, **kwargs):
    """Upload + GET: devolve o lote ja processado (CR-052)."""
    r = upload(client, transacoes=transacoes, **kwargs)
    assert r.status_code == 202, r.text
    batch_id = r.json()["batch"]["id"]
    r = client.get(f"/api/imports/{batch_id}")
    assert r.status_code == 200, r.text
    return r.json()


# ========== CR-048: parametros da geracao atual ==========

def _import_response(text: str, *, with_thinking: bool = True, stop_reason: str = "end_turn"):
    """Resposta mockada da API no formato da geracao atual (blocos tipados)."""
    response = MagicMock()
    blocks = [MagicMock(type="thinking", thinking="raciocinio")] if with_thinking else []
    blocks.append(MagicMock(type="text", text=text))
    response.content = blocks
    response.stop_reason = stop_reason
    response.usage.input_tokens = 9000
    response.usage.output_tokens = 3000
    return response


VALID_EXTRACTION = json.dumps({
    "banco": "Nubank",
    "tipo_documento": "fatura",
    "transacoes": [TX_PADARIA],
})


class TestModelMigration:
    """CR-048: migracao para Claude Opus 5 no servico de importacao."""

    @staticmethod
    def _run(mock_sdk, response=None):
        mock_client = MagicMock()
        mock_sdk.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = response or _import_response(VALID_EXTRACTION)
        return mock_client

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}, clear=True)
    @patch("app.import_service.anthropic_sdk")
    def test_nao_envia_temperature(self, mock_sdk):
        mock_client = self._run(mock_sdk)

        call_import_api(PDF_BYTES, "system", "user")

        kwargs = mock_client.messages.create.call_args.kwargs
        assert "temperature" not in kwargs
        assert "top_p" not in kwargs
        assert "top_k" not in kwargs

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}, clear=True)
    @patch("app.import_service.anthropic_sdk")
    def test_modelo_default_thinking_e_effort(self, mock_sdk):
        mock_client = self._run(mock_sdk)

        call_import_api(PDF_BYTES, "system", "user")

        kwargs = mock_client.messages.create.call_args.kwargs
        assert kwargs["model"] == DEFAULT_MODEL == "claude-opus-5"
        assert kwargs["thinking"] == {"type": "adaptive"}
        # effort baixo: extracao e mecanica — contem custo e latencia
        assert kwargs["output_config"] == {"effort": "low"}
        # max_tokens cobre raciocinio + JSON de uma fatura grande
        assert kwargs["max_tokens"] >= 16000

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}, clear=True)
    @patch("app.import_service.anthropic_sdk")
    def test_le_texto_apos_bloco_de_thinking(self, mock_sdk):
        response = _import_response(VALID_EXTRACTION, with_thinking=True)
        assert response.content[0].type == "thinking"
        self._run(mock_sdk, response)

        result = call_import_api(PDF_BYTES, "system", "user")

        assert result["resultado"]["banco"] == "Nubank"
        assert result["tokens_input"] == 9000

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test"}, clear=True)
    @patch("app.import_service.anthropic_sdk")
    def test_recusa_nao_faz_retry(self, mock_sdk):
        response = _import_response("", stop_reason="refusal")
        response.content = []
        mock_client = self._run(mock_sdk, response)

        with pytest.raises(AiRefusalError):
            call_import_api(PDF_BYTES, "system", "user")

        # PDF e caro para reenviar — a recusa nao pode consumir os retries
        assert mock_client.messages.create.call_count == 1


# ========== Unit: fingerprint ==========

class TestFingerprint:
    def test_normalize_description(self):
        assert normalize_description("  PADARIA   Stella \n") == "padaria stella"

    def test_same_transaction_same_fingerprint(self):
        f1 = compute_fingerprint("u1", date(2026, 7, 28), 23.5, "PADARIA STELLA")
        f2 = compute_fingerprint("u1", date(2026, 7, 28), 23.50, "padaria  stella")
        assert f1 == f2

    def test_different_user_or_value_changes_fingerprint(self):
        base = compute_fingerprint("u1", date(2026, 7, 28), 23.5, "PADARIA")
        assert compute_fingerprint("u2", date(2026, 7, 28), 23.5, "PADARIA") != base
        assert compute_fingerprint("u1", date(2026, 7, 28), 24.5, "PADARIA") != base


# ========== Unit: validate_ai_result ==========

class TestValidateAiResult:
    def test_happy_path(self):
        parsed = validate_ai_result(
            {"banco": "Nubank", "tipo_documento": "fatura", "transacoes": [TX_PADARIA]},
            valid_expense_ids=set(),
        )
        assert parsed["banco"] == "Nubank"
        assert parsed["tipo_documento"] == "fatura"
        tx = parsed["transacoes"][0]
        assert tx["data"] == date(2026, 7, 28)
        assert tx["categoria"] == "Alimentação"
        assert tx["subcategoria"] == "Padaria"

    def test_malformed_transactions_dropped(self):
        parsed = validate_ai_result(
            {
                "tipo_documento": "extrato",
                "transacoes": [
                    {"data": "invalida", "descricao": "X", "valor": 10},
                    {"data": "2026-07-01", "descricao": "", "valor": 10},
                    {"data": "2026-07-01", "descricao": "OK", "valor": -5},
                    {"data": "2026-07-01", "descricao": "OK", "valor": "abc"},
                    "nao-e-dict",
                ],
            },
            valid_expense_ids=set(),
        )
        assert parsed["transacoes"] == []

    def test_unknown_classification_becomes_gasto_diario(self):
        parsed = validate_ai_result(
            {"transacoes": [{**TX_PADARIA, "classificacao": "invento"}]},
            valid_expense_ids=set(),
        )
        assert parsed["transacoes"][0]["classificacao"] == "gasto_diario"

    def test_match_with_unknown_expense_id_becomes_gasto_diario(self):
        parsed = validate_ai_result(
            {"transacoes": [TX_MATCH_LUZ]},
            valid_expense_ids={"outro-id"},
        )
        tx = parsed["transacoes"][0]
        assert tx["classificacao"] == "gasto_diario"
        assert tx["expense_id_sugerido"] is None

    def test_match_with_valid_expense_id_kept(self):
        parsed = validate_ai_result(
            {"transacoes": [TX_MATCH_LUZ]},
            valid_expense_ids={"expense-luz"},
        )
        tx = parsed["transacoes"][0]
        assert tx["classificacao"] == "match_planejado"
        assert tx["expense_id_sugerido"] == "expense-luz"

    def test_invalid_category_pair_cleared(self):
        # "Streaming" existe, mas nao dentro de "Alimentação" — par invalido
        parsed = validate_ai_result(
            {"transacoes": [{**TX_PADARIA, "categoria": "Alimentação", "subcategoria": "Streaming"}]},
            valid_expense_ids=set(),
        )
        tx = parsed["transacoes"][0]
        assert tx["categoria"] is None
        assert tx["subcategoria"] is None

    def test_fatura_without_metodo_defaults_to_credito(self):
        parsed = validate_ai_result(
            {"tipo_documento": "fatura", "transacoes": [{**TX_PADARIA, "metodo_pagamento": None}]},
            valid_expense_ids=set(),
        )
        assert parsed["transacoes"][0]["metodo_pagamento"] == "Cartão de Crédito"

    def test_motivo_ignorar_cleared_for_non_ignorar(self):
        parsed = validate_ai_result(
            {"transacoes": [{**TX_PADARIA, "motivo_ignorar": "algo"}]},
            valid_expense_ids=set(),
        )
        assert parsed["transacoes"][0]["motivo_ignorar"] is None


# ========== Endpoint: upload ==========

class TestUpload:
    def test_upload_responde_202_com_lote_processando(self, client, open_expense):
        """CR-052: o corpo e serializado antes de a BackgroundTasks rodar."""
        r = upload(client)
        assert r.status_code == 202
        body = r.json()
        assert body["status"] == "disponivel"
        batch = body["batch"]
        assert batch["status"] == "processando"
        assert batch["transacoes"] == []
        assert batch["erro_mensagem"] is None

    def test_upload_happy_path(self, client, db, open_expense):
        batch = upload_batch(client)
        assert batch["status"] == "pendente_revisao"
        assert batch["banco_detectado"] == "Nubank"
        assert batch["tipo_documento"] == "fatura"
        assert len(batch["transacoes"]) == 3
        classificacoes = {t["classificacao"] for t in batch["transacoes"]}
        assert classificacoes == {"gasto_diario", "match_planejado", "ignorar"}
        # Persistido em staging
        assert db.query(ImportBatch).count() == 1
        assert db.query(ImportTransaction).count() == 3

    def test_upload_rejects_non_pdf_extension(self, client):
        r = client.post(
            "/api/imports",
            files={"file": ("extrato.csv", b"a,b,c", "text/csv")},
        )
        assert r.status_code == 422

    def test_upload_rejects_wrong_magic_bytes(self, client):
        r = client.post(
            "/api/imports",
            files={"file": ("fake.pdf", b"nao sou um pdf", "application/pdf")},
        )
        assert r.status_code == 422

    def test_upload_rejects_oversized_file(self, client):
        big = b"%PDF-" + b"0" * (10 * 1024 * 1024)
        r = client.post(
            "/api/imports",
            files={"file": ("grande.pdf", big, "application/pdf")},
        )
        assert r.status_code == 413

    def test_upload_disabled_flag(self, client, monkeypatch):
        monkeypatch.setenv("IMPORT_ENABLED", "false")
        r = upload(client)
        assert r.status_code == 200
        assert r.json()["status"] == "indisponivel"

    def test_upload_without_api_key(self, client, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        r = upload(client)
        assert r.status_code == 200
        assert r.json()["status"] == "indisponivel"

    def test_ai_error_grava_lote_em_erro(self, client, db):
        """CR-052: a falha da IA passa a ficar registrada no lote."""
        with patch("app.import_service.call_import_api", side_effect=TimeoutError("boom")):
            r = client.post(
                "/api/imports",
                files={"file": ("fatura.pdf", PDF_BYTES, "application/pdf")},
            )
        assert r.status_code == 202
        batch_id = r.json()["batch"]["id"]

        batch = client.get(f"/api/imports/{batch_id}").json()
        assert batch["status"] == "erro"
        assert batch["erro_mensagem"] == "Não foi possível interpretar o documento: TimeoutError"
        assert batch["transacoes"] == []
        # RN-043: a mensagem nao carrega conteudo do documento
        assert "boom" not in batch["erro_mensagem"]
        assert db.query(ImportTransaction).count() == 0

    def test_no_transactions_grava_lote_em_erro(self, client, db):
        batch = upload_batch(client, transacoes=[])
        assert batch["status"] == "erro"
        assert batch["erro_mensagem"] == "Nenhuma transação foi identificada no documento"
        assert db.query(ImportTransaction).count() == 0


# ========== CR-052: processamento assincrono ==========

class TestProcessamentoAssincrono:
    """RN-047/RN-048: extracao em BackgroundTasks e lote orfao."""

    def _batch_processando(self, db, user_id="user-a", minutos_atras=0):
        batch = ImportBatch(
            user_id=user_id,
            filename="fatura.pdf",
            status="processando",
            modelo="claude-test",
            created_at=datetime.now() - timedelta(minutes=minutos_atras),
        )
        db.add(batch)
        db.commit()
        return batch

    def test_task_grava_metadata_da_chamada(self, client, db):
        batch = upload_batch(client, transacoes=[TX_PADARIA])
        row = db.query(ImportBatch).filter_by(id=batch["id"]).one()
        assert row.tokens_input == 1000
        assert row.tokens_output == 500
        assert row.modelo == "claude-test"  # reescrito pela task
        assert row.tempo_processamento_ms == 1234

    def test_pending_inclui_processando(self, client, db):
        self._batch_processando(db)
        upload(client)  # gera um lote 'pendente_revisao'

        r = client.get("/api/imports/pending")
        assert r.status_code == 200
        statuses = {b["status"] for b in r.json()}
        assert statuses == {"processando", "pendente_revisao"}

    def test_lote_orfao_vira_erro_na_leitura(self, client, db):
        batch = self._batch_processando(db, minutos_atras=STALE_PROCESSING_MINUTES + 1)

        r = client.get(f"/api/imports/{batch.id}")
        assert r.status_code == 200
        assert r.json()["status"] == "erro"
        assert "interrompido" in r.json()["erro_mensagem"]
        # Persistido, nao so apresentado
        db.expire_all()
        assert db.query(ImportBatch).filter_by(id=batch.id).one().status == "erro"

    def test_lote_orfao_sai_do_pending(self, client, db):
        self._batch_processando(db, minutos_atras=STALE_PROCESSING_MINUTES + 1)

        r = client.get("/api/imports/pending")
        assert r.json() == []

    def test_processando_dentro_da_janela_permanece(self, client, db):
        batch = self._batch_processando(db, minutos_atras=STALE_PROCESSING_MINUTES - 1)

        r = client.get(f"/api/imports/{batch.id}")
        assert r.json()["status"] == "processando"
        assert len(client.get("/api/imports/pending").json()) == 1

    def test_lote_descartado_durante_extracao_nao_ressuscita(self, client, db):
        """A task nao pode sobrescrever uma decisao que o usuario ja tomou."""
        def descarta_durante_extracao(*args, **kwargs):
            row = db.query(ImportBatch).filter_by(status="processando").one()
            row.status = "descartado"
            db.commit()
            return ai_result([TX_PADARIA])

        with patch(
            "app.import_service.call_import_api", side_effect=descarta_durante_extracao
        ):
            r = client.post(
                "/api/imports",
                files={"file": ("fatura.pdf", PDF_BYTES, "application/pdf")},
            )
        assert r.status_code == 202

        db.expire_all()
        row = db.query(ImportBatch).filter_by(id=r.json()["batch"]["id"]).one()
        assert row.status == "descartado"
        assert db.query(ImportTransaction).count() == 0

    def test_lote_descartado_nao_vira_erro_quando_a_ia_falha(self, client, db):
        """A guarda vale tambem no caminho de erro, nao so no de sucesso."""
        def descarta_e_falha(*args, **kwargs):
            row = db.query(ImportBatch).filter_by(status="processando").one()
            row.status = "descartado"
            db.commit()
            raise TimeoutError("boom")

        with patch("app.import_service.call_import_api", side_effect=descarta_e_falha):
            r = client.post(
                "/api/imports",
                files={"file": ("fatura.pdf", PDF_BYTES, "application/pdf")},
            )
        assert r.status_code == 202

        db.expire_all()
        row = db.query(ImportBatch).filter_by(id=r.json()["batch"]["id"]).one()
        assert row.status == "descartado"
        assert row.erro_mensagem is None

    def test_confirm_em_lote_processando_retorna_409(self, client, db):
        batch = self._batch_processando(db)

        r = client.post(f"/api/imports/{batch.id}/confirm", json={"transacoes": []})
        assert r.status_code == 409

    def test_lote_de_outro_usuario_retorna_404(self, client, db, user_b):
        batch = self._batch_processando(db, user_id=user_b.id)

        assert client.get(f"/api/imports/{batch.id}").status_code == 404


# ========== Endpoint: confirm ==========

class TestConfirm:
    def _upload_batch(self, client):
        return upload_batch(client)

    def _tx_by_class(self, batch, classificacao):
        return next(t for t in batch["transacoes"] if t["classificacao"] == classificacao)

    def test_confirm_creates_daily_and_updates_expense(self, client, db, open_expense):
        batch = self._upload_batch(client)
        tx_gasto = self._tx_by_class(batch, "gasto_diario")
        tx_match = self._tx_by_class(batch, "match_planejado")

        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={
                "transacoes": [
                    {"id": tx_gasto["id"], "acao": "criar_gasto_diario"},
                    {"id": tx_match["id"], "acao": "atualizar_planejado"},
                ]
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body == {
            "gastos_diarios_criados": 1,
            "planejados_criados": 0,  # CR-049: nenhum parcelamento neste lote
            "planejados_atualizados": 1,
            "descartadas": 1,  # a transacao 'ignorar' ausente do payload
        }

        # Gasto diario criado no mes da DATA DA COMPRA (RN-039)
        gasto = db.query(DailyExpense).one()
        assert gasto.data == date(2026, 7, 28)
        assert gasto.mes_referencia == date(2026, 7, 1)
        assert gasto.categoria == "Alimentação"
        assert gasto.metodo_pagamento == "Cartão de Crédito"

        # Planejado atualizado (RN-040): status Pago + valor real
        db.refresh(open_expense)
        assert open_expense.status == ExpenseStatus.PAGO.value
        assert float(open_expense.valor) == 187.32

        # Auditoria + status do lote
        db_batch = db.query(ImportBatch).one()
        assert db_batch.status == "confirmado"
        db_tx_gasto = db.query(ImportTransaction).filter_by(id=tx_gasto["id"]).one()
        assert db_tx_gasto.status == "confirmada"
        assert db_tx_gasto.daily_expense_id_criado == gasto.id
        db_tx_match = db.query(ImportTransaction).filter_by(id=tx_match["id"]).one()
        assert db_tx_match.expense_id_atualizado == open_expense.id

    def test_confirm_with_edited_values(self, client, db, open_expense):
        batch = self._upload_batch(client)
        tx_gasto = self._tx_by_class(batch, "gasto_diario")
        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={
                "transacoes": [
                    {
                        "id": tx_gasto["id"],
                        "acao": "criar_gasto_diario",
                        "descricao": "Padaria da esquina",
                        "valor": 25.00,
                        "categoria": "Alimentação",
                        "subcategoria": "Café",
                        "metodo_pagamento": "Pix",
                    },
                ]
            },
        )
        assert r.status_code == 200
        gasto = db.query(DailyExpense).one()
        assert gasto.descricao == "Padaria da esquina"
        assert float(gasto.valor) == 25.00
        assert gasto.subcategoria == "Café"
        assert gasto.metodo_pagamento == "Pix"

    def test_confirm_invalid_category_pair_rejected_atomically(self, client, db, open_expense):
        batch = self._upload_batch(client)
        tx_gasto = self._tx_by_class(batch, "gasto_diario")
        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={
                "transacoes": [
                    {
                        "id": tx_gasto["id"],
                        "acao": "criar_gasto_diario",
                        "categoria": "Alimentação",
                        "subcategoria": "Streaming",  # par invalido
                    },
                ]
            },
        )
        assert r.status_code == 422
        # Atomicidade: nada persistido
        assert db.query(DailyExpense).count() == 0
        assert db.query(ImportBatch).one().status == "pendente_revisao"

    def test_confirm_unknown_transaction_rejected(self, client, open_expense):
        batch = self._upload_batch(client)
        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={"transacoes": [{"id": "tx-inexistente", "acao": "descartar"}]},
        )
        assert r.status_code == 422

    def test_confirm_already_confirmed_returns_409(self, client, open_expense):
        batch = self._upload_batch(client)
        r1 = client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": []})
        assert r1.status_code == 200
        r2 = client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": []})
        assert r2.status_code == 409

    def test_confirm_same_expense_twice_returns_422(self, client, db, open_expense):
        """Code review CR-046: duas decisoes atualizar_planejado para o mesmo expense_id."""
        batch = self._upload_batch(client)
        tx_gasto = self._tx_by_class(batch, "gasto_diario")
        tx_match = self._tx_by_class(batch, "match_planejado")
        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={
                "transacoes": [
                    {"id": tx_match["id"], "acao": "atualizar_planejado", "expense_id": "expense-luz", "valor": 100.00},
                    {"id": tx_gasto["id"], "acao": "atualizar_planejado", "expense_id": "expense-luz", "valor": 90.00},
                ]
            },
        )
        assert r.status_code == 422
        # Atomicidade: nada persistido
        db.refresh(open_expense)
        assert open_expense.status == ExpenseStatus.PENDENTE.value
        assert float(open_expense.valor) == 200.00

    def test_confirm_blank_descricao_returns_422(self, client, db, open_expense):
        """Code review CR-046: descricao=' ' passa no min_length mas vira vazia apos strip."""
        batch = self._upload_batch(client)
        tx_gasto = self._tx_by_class(batch, "gasto_diario")
        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={
                "transacoes": [
                    {"id": tx_gasto["id"], "acao": "criar_gasto_diario", "descricao": " "},
                ]
            },
        )
        assert r.status_code == 422
        assert db.query(DailyExpense).count() == 0

    def test_confirm_expense_of_another_user_returns_404(self, client, db, open_expense, user_b):
        other_expense = Expense(
            id="expense-user-b",
            user_id=user_b.id,
            mes_referencia=date(2026, 7, 1),
            nome="Conta B",
            valor=100.00,
            vencimento=date(2026, 7, 10),
            recorrente=True,
            status=ExpenseStatus.PENDENTE.value,
        )
        db.add(other_expense)
        db.commit()

        batch = self._upload_batch(client)
        tx_match = self._tx_by_class(batch, "match_planejado")
        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={
                "transacoes": [
                    {"id": tx_match["id"], "acao": "atualizar_planejado", "expense_id": "expense-user-b"},
                ]
            },
        )
        assert r.status_code == 404


# ========== CR-049: compras parceladas (F07 E-A) ==========

class TestParcelamentoValidacao:
    """Sanitizacao dos campos de parcela em validate_ai_result."""

    def test_parcelamento_valido_preserva_numeracao(self):
        parsed = validate_ai_result(
            {"transacoes": [TX_PARCELAMENTO]}, valid_expense_ids=set()
        )
        tx = parsed["transacoes"][0]
        assert tx["classificacao"] == "parcelamento"
        assert tx["parcela_atual"] == 3
        assert tx["parcela_total"] == 10

    @pytest.mark.parametrize(
        "parcelas",
        [
            {"parcela_atual": None, "parcela_total": None},   # sem numeracao
            {"parcela_atual": 3, "parcela_total": None},      # incompleta
            {"parcela_atual": 11, "parcela_total": 10},       # atual > total
            {"parcela_atual": 1, "parcela_total": 1},         # 1/1 nao e parcelamento
            {"parcela_atual": 0, "parcela_total": 10},        # atual < 1
            {"parcela_atual": "tres", "parcela_total": "dez"},  # nao inteiros
        ],
    )
    def test_numeracao_incoerente_vira_gasto_diario(self, parcelas):
        parsed = validate_ai_result(
            {"transacoes": [{**TX_PARCELAMENTO, **parcelas}]}, valid_expense_ids=set()
        )
        tx = parsed["transacoes"][0]
        assert tx["classificacao"] == "gasto_diario"
        assert tx["parcela_atual"] is None
        assert tx["parcela_total"] is None

    def test_parcelas_ignoradas_em_outras_classificacoes(self):
        """Numeracao so vale em 'parcelamento' — nao contamina gasto_diario."""
        parsed = validate_ai_result(
            {"transacoes": [{**TX_PADARIA, "parcela_atual": 3, "parcela_total": 10}]},
            valid_expense_ids=set(),
        )
        tx = parsed["transacoes"][0]
        assert tx["classificacao"] == "gasto_diario"
        assert tx["parcela_atual"] is None


class TestParcelamentoConfirm:
    """Confirmacao da acao criar_planejado_parcelado."""

    def _upload_parcelamento(self, client):
        return upload_batch(client, transacoes=[TX_PARCELAMENTO])

    def _decisao(self, tx_id, **overrides):
        decisao = {
            "id": tx_id,
            "acao": "criar_planejado_parcelado",
            "parcela_atual": 3,
            "parcela_total": 10,
        }
        decisao.update(overrides)
        return decisao

    def test_cria_serie_de_parcelas(self, client, db):
        batch = self._upload_parcelamento(client)
        tx = batch["transacoes"][0]
        assert tx["classificacao"] == "parcelamento"
        assert tx["parcela_atual"] == 3

        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={"transacoes": [self._decisao(tx["id"])]},
        )
        assert r.status_code == 200
        assert r.json()["planejados_criados"] == 8  # parcelas 3..10
        assert r.json()["gastos_diarios_criados"] == 0

        parcelas = db.query(Expense).order_by(Expense.parcela_atual).all()
        assert [p.parcela_atual for p in parcelas] == [3, 4, 5, 6, 7, 8, 9, 10]
        assert all(p.nome == "Netshoes" for p in parcelas)
        assert all(p.parcela_total == 10 for p in parcelas)
        assert all(p.recorrente is False for p in parcelas)

    def test_parcela_atual_nasce_paga_e_futuras_pendentes(self, client, db):
        """RN-044: a parcela desta fatura ja foi cobrada."""
        batch = self._upload_parcelamento(client)
        tx = batch["transacoes"][0]

        client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={"transacoes": [self._decisao(tx["id"])]},
        )

        parcelas = db.query(Expense).order_by(Expense.parcela_atual).all()
        assert parcelas[0].status == ExpenseStatus.PAGO.value
        assert all(p.status == ExpenseStatus.PENDENTE.value for p in parcelas[1:])

    def test_mes_e_vencimento_avancam_a_partir_da_data_da_compra(self, client, db):
        """RN-045: compra em 15/07/2026; a parcela 3 e cobrada 2 meses depois."""
        batch = self._upload_parcelamento(client)
        tx = batch["transacoes"][0]

        client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={"transacoes": [self._decisao(tx["id"])]},
        )

        parcelas = db.query(Expense).order_by(Expense.parcela_atual).all()
        # parcela 3 = compra + 2 meses (nao o mes da compra)
        assert parcelas[0].mes_referencia == date(2026, 9, 1)
        assert parcelas[0].vencimento == date(2026, 9, 15)
        # parcela 10 = compra + 9 meses
        assert parcelas[-1].mes_referencia == date(2027, 4, 1)
        assert parcelas[-1].vencimento == date(2027, 4, 15)

    def test_nao_recria_parcela_ja_existente(self, client, db, user_a):
        """RN-046: importar a fatura do mes seguinte nao duplica a serie."""
        db.add(
            Expense(
                user_id=user_a.id,
                mes_referencia=date(2026, 10, 1),
                nome="Netshoes",
                valor=149.90,
                vencimento=date(2026, 10, 15),
                parcela_atual=4,
                parcela_total=10,
                recorrente=False,
                status=ExpenseStatus.PENDENTE.value,
            )
        )
        db.commit()

        batch = self._upload_parcelamento(client)
        tx = batch["transacoes"][0]
        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={"transacoes": [self._decisao(tx["id"])]},
        )

        assert r.json()["planejados_criados"] == 7  # a parcela 4 ja existia
        parcelas_4 = db.query(Expense).filter(Expense.parcela_atual == 4).all()
        assert len(parcelas_4) == 1

    def test_reimportar_a_propria_parcela_nao_duplica(self, client, db, user_a):
        """RN-046: fatura seguinte com a parcela ja criada concilia, nao duplica."""
        for parcela in (3, 4):
            # compra em 15/07: parcela 3 em set, parcela 4 em out
            db.add(
                Expense(
                    user_id=user_a.id,
                    mes_referencia=date(2026, 6 + parcela, 1),
                    nome="Netshoes",
                    valor=149.90,
                    vencimento=date(2026, 6 + parcela, 15),
                    parcela_atual=parcela,
                    parcela_total=10,
                    recorrente=False,
                    status=ExpenseStatus.PENDENTE.value,
                )
            )
        db.commit()

        batch = self._upload_parcelamento(client)
        tx_id = batch["transacoes"][0]["id"]
        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={"transacoes": [self._decisao(tx_id)]},
        )

        # 3 e 4 ja existiam: cria apenas 5..10
        assert r.json()["planejados_criados"] == 6
        parcelas_3 = db.query(Expense).filter(Expense.parcela_atual == 3).all()
        assert len(parcelas_3) == 1
        # a parcela desta fatura foi conciliada (RN-044), nao duplicada
        assert parcelas_3[0].status == ExpenseStatus.PAGO.value

    def test_auditoria_grava_expense_id_criado(self, client, db):
        batch = self._upload_parcelamento(client)
        tx_id = batch["transacoes"][0]["id"]

        client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={"transacoes": [self._decisao(tx_id)]},
        )

        tx_db = db.query(ImportTransaction).filter(ImportTransaction.id == tx_id).one()
        assert tx_db.status == "confirmada"
        parcela_atual = db.query(Expense).filter(Expense.parcela_atual == 3).one()
        assert tx_db.expense_id_criado == parcela_atual.id

    @pytest.mark.parametrize(
        "parcelas",
        [
            {"parcela_atual": None, "parcela_total": None},  # obrigatorios
            {"parcela_atual": 3, "parcela_total": None},
            {"parcela_atual": 11, "parcela_total": 10},      # atual > total
            {"parcela_atual": 1, "parcela_total": 1},        # serie exige 2+
        ],
    )
    def test_numeracao_invalida_no_confirm_retorna_422(self, client, db, parcelas):
        batch = self._upload_parcelamento(client)
        tx_id = batch["transacoes"][0]["id"]

        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={"transacoes": [self._decisao(tx_id, **parcelas)]},
        )

        assert r.status_code == 422
        assert db.query(Expense).count() == 0  # nada gravado

    def test_categoria_invalida_retorna_422(self, client, db):
        batch = self._upload_parcelamento(client)
        tx_id = batch["transacoes"][0]["id"]

        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={
                "transacoes": [
                    self._decisao(tx_id, categoria="Alimentação", subcategoria="Roupas")
                ]
            },
        )

        assert r.status_code == 422
        assert db.query(Expense).count() == 0

    def test_usuario_pode_rebaixar_parcelamento_para_gasto_diario(self, client, db):
        """A revisao manda no destino: parcelamento pode virar gasto diario."""
        batch = self._upload_parcelamento(client)
        tx_id = batch["transacoes"][0]["id"]

        r = client.post(
            f"/api/imports/{batch['id']}/confirm",
            json={
                "transacoes": [
                    {
                        "id": tx_id,
                        "acao": "criar_gasto_diario",
                        "categoria": "Compras Pessoais",
                        "subcategoria": "Roupas",
                        "metodo_pagamento": "Cartão de Crédito",
                    }
                ]
            },
        )

        assert r.status_code == 200
        assert r.json() == {
            "gastos_diarios_criados": 1,
            "planejados_criados": 0,
            "planejados_atualizados": 0,
            "descartadas": 0,
        }
        assert db.query(Expense).count() == 0
        assert db.query(DailyExpense).count() == 1


class TestParcelamentoCodeReview:
    """Findings do code review pre-merge do CR-049."""

    def test_fingerprint_distingue_parcelas_da_mesma_compra(self):
        """Parcelas da mesma compra compartilham data/valor/descricao limpa."""
        base = ("user-a", date(2026, 7, 15), 149.90, "Netshoes")
        fp3 = compute_fingerprint(*base, 3, 10)
        fp4 = compute_fingerprint(*base, 4, 10)
        assert fp3 != fp4
        # sem numeracao, a formula original (fingerprints antigos seguem validos)
        assert compute_fingerprint(*base) == compute_fingerprint(*base, None, None)

    def test_parcela_seguinte_nao_nasce_duplicada(self, client, db):
        """Sem o fix, a parcela 4 do mes seguinte viria marcada 'duplicada'."""
        b1 = upload_batch(client, transacoes=[TX_PARCELAMENTO])
        client.post(f"/api/imports/{b1['id']}/confirm", json={"transacoes": [
            {"id": b1["transacoes"][0]["id"], "acao": "criar_planejado_parcelado",
             "parcela_atual": 3, "parcela_total": 10}]})

        b2 = upload_batch(client, transacoes=[{**TX_PARCELAMENTO, "parcela_atual": 4}])
        assert b2["transacoes"][0]["status"] == "pendente"

    def test_parcela_total_absurdo_rejeitado(self, client, db):
        """Teto de parcelas evita criar milhares de despesas num request."""
        batch = upload_batch(client, transacoes=[TX_PARCELAMENTO])
        r = client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": [
            {"id": batch["transacoes"][0]["id"], "acao": "criar_planejado_parcelado",
             "parcela_atual": 1, "parcela_total": 200000}]})
        assert r.status_code == 422
        assert db.query(Expense).count() == 0

    def test_duas_linhas_para_a_mesma_serie_retorna_422(self, client, db):
        """Sem a guarda, a segunda linha sobrescreveria a despesa da primeira."""
        tx_b = {**TX_PARCELAMENTO, "valor": 300.00}
        batch = upload_batch(client, transacoes=[TX_PARCELAMENTO, tx_b])
        ids = [t["id"] for t in batch["transacoes"]]
        r = client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": [
            {"id": ids[0], "acao": "criar_planejado_parcelado", "parcela_atual": 3, "parcela_total": 10},
            {"id": ids[1], "acao": "criar_planejado_parcelado", "parcela_atual": 3, "parcela_total": 10}]})
        assert r.status_code == 422
        assert "outra transação deste lote" in r.json()["detail"]
        assert db.query(Expense).count() == 0

    def test_categoria_limpa_na_revisao_nao_volta_da_ia(self, client, db):
        """Usuario que limpa a categoria nao recebe o palpite da IA de volta."""
        batch = upload_batch(client, transacoes=[TX_PARCELAMENTO])
        assert batch["transacoes"][0]["categoria"] == "Compras Pessoais"

        client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": [
            {"id": batch["transacoes"][0]["id"], "acao": "criar_planejado_parcelado",
             "parcela_atual": 3, "parcela_total": 10}]})  # sem categoria no payload

        parcela = db.query(Expense).filter(Expense.parcela_atual == 3).one()
        assert parcela.categoria is None
        assert parcela.subcategoria is None


# ========== Dedup (RN-042) ==========

class TestDedup:
    def test_confirmed_transactions_marked_duplicada_on_reupload(self, client, db, open_expense):
        batch1 = upload_batch(client)
        tx_gasto = next(t for t in batch1["transacoes"] if t["classificacao"] == "gasto_diario")
        r = client.post(
            f"/api/imports/{batch1['id']}/confirm",
            json={"transacoes": [{"id": tx_gasto["id"], "acao": "criar_gasto_diario"}]},
        )
        assert r.status_code == 200

        # Re-upload do mesmo documento
        batch2 = upload_batch(client)
        by_desc = {t["descricao"]: t for t in batch2["transacoes"]}
        assert by_desc["PADARIA STELLA"]["status"] == "duplicada"
        # As nao confirmadas (descartadas no 1o lote) continuam pendentes
        assert by_desc["CEMIG ENERGIA"]["status"] == "pendente"
        assert by_desc["PAGAMENTO RECEBIDO"]["status"] == "pendente"

    def test_duplicada_absent_from_confirm_stays_duplicada(self, client, db, open_expense):
        """Code review CR-046: duplicada nao resgatada permanece 'duplicada' (nao vira descartada)."""
        batch1 = upload_batch(client)
        tx_gasto = next(t for t in batch1["transacoes"] if t["classificacao"] == "gasto_diario")
        client.post(
            f"/api/imports/{batch1['id']}/confirm",
            json={"transacoes": [{"id": tx_gasto["id"], "acao": "criar_gasto_diario"}]},
        )

        batch2 = upload_batch(client)
        r = client.post(f"/api/imports/{batch2['id']}/confirm", json={"transacoes": []})
        assert r.status_code == 200
        assert r.json()["descartadas"] == 2  # duplicada nao conta como descartada

        db_tx = (
            db.query(ImportTransaction)
            .filter_by(batch_id=batch2["id"], descricao="PADARIA STELLA")
            .one()
        )
        assert db_tx.status == "duplicada"


# ========== Ownership / pending / delete ==========

class TestOwnershipAndLifecycle:
    def test_get_batch_of_another_user_returns_404(self, client, db, user_b, open_expense):
        batch = upload_batch(client)
        # Troca o usuario autenticado para user_b
        app.dependency_overrides[get_current_user] = lambda: user_b
        assert client.get(f"/api/imports/{batch['id']}").status_code == 404
        assert client.post(
            f"/api/imports/{batch['id']}/confirm", json={"transacoes": []}
        ).status_code == 404
        assert client.delete(f"/api/imports/{batch['id']}").status_code == 404

    def test_pending_lists_only_pending_batches(self, client, open_expense):
        batch = upload_batch(client)
        r = client.get("/api/imports/pending")
        assert r.status_code == 200
        assert [b["id"] for b in r.json()] == [batch["id"]]

        client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": []})
        assert client.get("/api/imports/pending").json() == []

    def test_get_batch_returns_transactions(self, client, open_expense):
        batch = upload_batch(client)
        r = client.get(f"/api/imports/{batch['id']}")
        assert r.status_code == 200
        assert len(r.json()["transacoes"]) == 3

    def test_delete_discards_pending_batch(self, client, db, open_expense):
        batch = upload_batch(client)
        r = client.delete(f"/api/imports/{batch['id']}")
        assert r.status_code == 204
        db_batch = db.query(ImportBatch).one()
        assert db_batch.status == "descartado"
        assert all(t.status == "descartada" for t in db_batch.transacoes)

    def test_delete_confirmed_batch_returns_409(self, client, open_expense):
        batch = upload_batch(client)
        client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": []})
        assert client.delete(f"/api/imports/{batch['id']}").status_code == 409
