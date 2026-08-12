"""
CR-046 (F07): Testes da importacao de extratos/faturas em PDF via IA.
API Anthropic sempre mockada (call_import_api).
"""
import pytest
from datetime import date
from unittest.mock import patch

from starlette.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
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
from app.import_service import (
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

TX_IGNORAR = {
    "data": "2026-07-05",
    "descricao": "PAGAMENTO RECEBIDO",
    "valor": 2500.00,
    "classificacao": "ignorar",
    "motivo_ignorar": "pagamento de fatura",
}


def upload(client, transacoes=None, **kwargs):
    if transacoes is None:
        transacoes = [TX_PADARIA, TX_MATCH_LUZ, TX_IGNORAR]
    result = ai_result(transacoes, **kwargs)
    with patch("app.import_service.call_import_api", return_value=result):
        return client.post(
            "/api/imports",
            files={"file": ("fatura.pdf", PDF_BYTES, "application/pdf")},
        )


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
    def test_upload_happy_path(self, client, db, open_expense):
        r = upload(client)
        assert r.status_code == 201
        body = r.json()
        assert body["status"] == "disponivel"
        batch = body["batch"]
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

    def test_upload_ai_error_returns_erro_without_batch(self, client, db):
        with patch("app.import_service.call_import_api", side_effect=TimeoutError("boom")):
            r = client.post(
                "/api/imports",
                files={"file": ("fatura.pdf", PDF_BYTES, "application/pdf")},
            )
        assert r.status_code == 200
        assert r.json()["status"] == "erro"
        assert db.query(ImportBatch).count() == 0

    def test_upload_no_transactions_returns_erro(self, client, db):
        r = upload(client, transacoes=[])
        assert r.status_code == 200
        assert r.json()["status"] == "erro"
        assert db.query(ImportBatch).count() == 0


# ========== Endpoint: confirm ==========

class TestConfirm:
    def _upload_batch(self, client):
        r = upload(client)
        assert r.status_code == 201
        return r.json()["batch"]

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


# ========== Dedup (RN-042) ==========

class TestDedup:
    def test_confirmed_transactions_marked_duplicada_on_reupload(self, client, db, open_expense):
        batch1 = upload(client).json()["batch"]
        tx_gasto = next(t for t in batch1["transacoes"] if t["classificacao"] == "gasto_diario")
        r = client.post(
            f"/api/imports/{batch1['id']}/confirm",
            json={"transacoes": [{"id": tx_gasto["id"], "acao": "criar_gasto_diario"}]},
        )
        assert r.status_code == 200

        # Re-upload do mesmo documento
        batch2 = upload(client).json()["batch"]
        by_desc = {t["descricao"]: t for t in batch2["transacoes"]}
        assert by_desc["PADARIA STELLA"]["status"] == "duplicada"
        # As nao confirmadas (descartadas no 1o lote) continuam pendentes
        assert by_desc["CEMIG ENERGIA"]["status"] == "pendente"
        assert by_desc["PAGAMENTO RECEBIDO"]["status"] == "pendente"


# ========== Ownership / pending / delete ==========

class TestOwnershipAndLifecycle:
    def test_get_batch_of_another_user_returns_404(self, client, db, user_b, open_expense):
        batch = upload(client).json()["batch"]
        # Troca o usuario autenticado para user_b
        app.dependency_overrides[get_current_user] = lambda: user_b
        assert client.get(f"/api/imports/{batch['id']}").status_code == 404
        assert client.post(
            f"/api/imports/{batch['id']}/confirm", json={"transacoes": []}
        ).status_code == 404
        assert client.delete(f"/api/imports/{batch['id']}").status_code == 404

    def test_pending_lists_only_pending_batches(self, client, open_expense):
        batch = upload(client).json()["batch"]
        r = client.get("/api/imports/pending")
        assert r.status_code == 200
        assert [b["id"] for b in r.json()] == [batch["id"]]

        client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": []})
        assert client.get("/api/imports/pending").json() == []

    def test_get_batch_returns_transactions(self, client, open_expense):
        batch = upload(client).json()["batch"]
        r = client.get(f"/api/imports/{batch['id']}")
        assert r.status_code == 200
        assert len(r.json()["transacoes"]) == 3

    def test_delete_discards_pending_batch(self, client, db, open_expense):
        batch = upload(client).json()["batch"]
        r = client.delete(f"/api/imports/{batch['id']}")
        assert r.status_code == 204
        db_batch = db.query(ImportBatch).one()
        assert db_batch.status == "descartado"
        assert all(t.status == "descartada" for t in db_batch.transacoes)

    def test_delete_confirmed_batch_returns_409(self, client, open_expense):
        batch = upload(client).json()["batch"]
        client.post(f"/api/imports/{batch['id']}/confirm", json={"transacoes": []})
        assert client.delete(f"/api/imports/{batch['id']}").status_code == 409
