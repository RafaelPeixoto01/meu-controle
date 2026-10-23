"""CR-058: API de integracao para o Lumi (RF-22, RN-054, ADR-023).

Sem override de autenticacao: as rotas usam o token de integracao de verdade.
"""
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app import crud
from app.auth import create_access_token, generate_integration_token
from app.database import Base, get_db
from app.main import app
from app.models import DailyExpense, Expense, ExpenseStatus, Income, IntegrationToken, User
from app.rate_limit import limiter, reset_integration_limits
from app.utils import add_months

TODAY = date.today()
THIS_MONTH = TODAY.replace(day=1)


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.fixture
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def users(db):
    user_a = User(id="user-a", nome="A", email="a@example.com", password_hash="x", email_verified=True)
    user_b = User(id="user-b", nome="B", email="b@example.com", password_hash="x", email_verified=True)
    db.add_all([user_a, user_b])
    db.commit()
    return user_a, user_b


@pytest.fixture
def client(session_factory, users):
    limiter.reset()
    reset_integration_limits()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def issue_token(db, user_id: str) -> str:
    token, prefix, token_hash = generate_integration_token()
    crud.create_integration_token(
        db, IntegrationToken(user_id=user_id, name="Lumi", prefix=prefix, token_hash=token_hash)
    )
    return token


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def add_expense(db, user_id: str, nome: str, valor: float, status: str = "Pendente") -> str:
    expense = Expense(
        user_id=user_id,
        mes_referencia=THIS_MONTH,
        nome=nome,
        valor=valor,
        vencimento=add_months(THIS_MONTH, 1) - timedelta(days=1),  # fim do mes: nao vira Atrasado
        recorrente=True,
        status=status,
    )
    db.add(expense)
    db.commit()
    return expense.id


def add_daily(db, user_id: str, dia: date, valor: float, subcategoria: str, categoria: str) -> None:
    db.add(
        DailyExpense(
            user_id=user_id,
            mes_referencia=dia.replace(day=1),
            descricao=subcategoria,
            valor=valor,
            data=dia,
            categoria=categoria,
            subcategoria=subcategoria,
            metodo_pagamento="Pix",
        )
    )
    db.commit()


# ---------- autenticacao ----------


def test_token_opens_only_the_integration_api(client, db, users):
    token = issue_token(db, "user-a")

    assert client.get("/api/integration/v1/categories", headers=bearer(token)).status_code == 200
    # o token de integracao nao abre as rotas do app
    year, month = THIS_MONTH.year, THIS_MONTH.month
    assert client.get(f"/api/months/{year}/{month}", headers=bearer(token)).status_code == 401
    assert client.get("/api/integration-tokens", headers=bearer(token)).status_code == 401


def test_login_jwt_and_bad_tokens_are_refused(client, db, users):
    jwt = create_access_token({"sub": "user-a", "email": "a@example.com"})
    for headers in (
        bearer(jwt),
        bearer("mc_nao-existe"),
        bearer("qualquer-coisa"),
        {},
    ):
        response = client.get("/api/integration/v1/categories", headers=headers)
        assert response.status_code == 401
        assert response.json() == {"detail": "Token de integração inválido"}


def test_revoked_token_stops_working_at_once(client, db, users):
    token = issue_token(db, "user-a")
    [row] = crud.get_active_integration_tokens(db, "user-a")
    row.revoked_at = datetime.now()
    db.commit()
    assert client.get("/api/integration/v1/categories", headers=bearer(token)).status_code == 401


def test_deleted_user_takes_the_tokens_along(client, db, users):
    token = issue_token(db, "user-a")
    db.delete(users[0])
    db.commit()
    assert crud.get_active_integration_tokens(db, "user-a") == []
    assert client.get("/api/integration/v1/categories", headers=bearer(token)).status_code == 401


def test_last_used_at_is_recorded_at_most_once_a_minute(client, db, users):
    token = issue_token(db, "user-a")
    client.get("/api/integration/v1/categories", headers=bearer(token))
    [row] = crud.get_active_integration_tokens(db, "user-a")
    db.refresh(row)
    first = row.last_used_at
    assert first is not None

    client.get("/api/integration/v1/categories", headers=bearer(token))
    db.refresh(row)
    assert row.last_used_at == first  # menos de um minuto depois: sem nova escrita

    row.last_used_at = first - timedelta(minutes=2)
    db.commit()
    client.get("/api/integration/v1/categories", headers=bearer(token))
    db.refresh(row)
    assert row.last_used_at > first - timedelta(minutes=2)


def test_rate_limit_of_60_calls_a_minute_per_token_across_all_routes(client, db, users):
    token = issue_token(db, "user-a")
    other = issue_token(db, "user-a")
    summary = "/api/integration/v1/daily-expenses/summary"
    period = {"de": THIS_MONTH.isoformat(), "ate": THIS_MONTH.isoformat()}
    for i in range(60):  # metade em cada rota: o limite e um so para o router
        if i % 2:
            assert client.get(summary, headers=bearer(token), params=period).status_code == 200
        else:
            assert client.get("/api/integration/v1/categories", headers=bearer(token)).status_code == 200
    month = f"/api/integration/v1/months/{THIS_MONTH.year}/{THIS_MONTH.month}"
    limited = client.get(month, headers=bearer(token))
    assert limited.status_code == 429
    assert limited.json() == {"detail": "Muitas requisições: tente de novo em instantes"}
    # outra grafia do esquema nao abre um contador novo para o mesmo token
    lower = client.get(month, headers={"Authorization": f"bearer {token}"})
    assert lower.status_code == 429
    # outro token tem o seu contador
    assert client.get("/api/integration/v1/categories", headers=bearer(other)).status_code == 200


def test_rate_limit_runs_before_auth_and_per_ip(client, db, users):
    """Tokens inventados nunca contam por token; o limite por IP (120/min) os segura."""
    statuses = [
        client.get("/api/integration/v1/categories", headers=bearer(f"mc_inventado-{i}")).status_code
        for i in range(121)
    ]
    assert statuses[:120] == [401] * 120
    assert statuses[120] == 429


# ---------- rotas ----------


def test_categories_are_the_app_ones(client, db, users):
    body = client.get("/api/integration/v1/categories", headers=bearer(issue_token(db, "user-a"))).json()
    assert "Supermercado" in body["categorias"]["Alimentação"]
    assert "Pix" in body["metodos_pagamento"]


def test_create_daily_expense_in_the_month_of_its_date(client, db, users):
    token = issue_token(db, "user-a")
    last_month_day = add_months(THIS_MONTH, -1).replace(day=20)

    response = client.post(
        "/api/integration/v1/daily-expenses",
        headers=bearer(token),
        json={
            "descricao": "Padaria",
            "valor": 45.0,
            "data": last_month_day.isoformat(),
            "subcategoria": "Padaria",
            "metodo_pagamento": "Pix",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["categoria"] == "Alimentação"
    assert body["mes_referencia"] == last_month_day.replace(day=1).isoformat()
    stored = crud.get_daily_expenses_by_month(db, last_month_day.replace(day=1), "user-a")
    assert [(g.descricao, float(g.valor)) for g in stored] == [("Padaria", 45.0)]


@pytest.mark.parametrize(
    "change",
    [
        {"subcategoria": "Padoca"},
        {"metodo_pagamento": "Cheque"},
        {"valor": 0},
        {"descricao": ""},
        {"valor": 50_000.01},  # valor mal ouvido
        {"data": (TODAY + timedelta(days=2)).isoformat()},  # data futura
        {"data": (TODAY - timedelta(days=367)).isoformat()},  # data antiga demais
    ],
)
def test_create_daily_expense_validation(client, db, users, change):
    payload = {
        "descricao": "Padaria",
        "valor": 45.0,
        "data": TODAY.isoformat(),
        "subcategoria": "Padaria",
        "metodo_pagamento": "Pix",
    } | change
    response = client.post(
        "/api/integration/v1/daily-expenses", headers=bearer(issue_token(db, "user-a")), json=payload
    )
    assert response.status_code == 422


def test_period_summary_by_date_category_and_subcategory(client, db, users):
    token = issue_token(db, "user-a")
    add_daily(db, "user-a", THIS_MONTH, 100.0, "Supermercado", "Alimentação")
    add_daily(db, "user-a", THIS_MONTH, 20.5, "Padaria", "Alimentação")
    add_daily(db, "user-a", THIS_MONTH, 30.0, "Combustível", "Transporte")
    add_daily(db, "user-a", THIS_MONTH - timedelta(days=1), 999.0, "Supermercado", "Alimentação")
    add_daily(db, "user-b", THIS_MONTH, 777.0, "Supermercado", "Alimentação")  # outro usuario

    url = "/api/integration/v1/daily-expenses/summary"
    period = {"de": THIS_MONTH.isoformat(), "ate": THIS_MONTH.isoformat()}
    body = client.get(url, headers=bearer(token), params=period).json()

    assert body["total"] == 150.5 and body["quantidade"] == 3
    assert body["por_categoria"] == {"Alimentação": 120.5, "Transporte": 30.0}
    assert body["por_subcategoria"] == {"Supermercado": 100.0, "Padaria": 20.5, "Combustível": 30.0}
    only = client.get(url, headers=bearer(token), params=period | {"subcategoria": "Supermercado"})
    assert only.json()["total"] == 100.0
    by_category = client.get(url, headers=bearer(token), params=period | {"categoria": "Transporte"})
    assert by_category.json()["total"] == 30.0


def test_period_summary_limits(client, db, users):
    token = issue_token(db, "user-a")
    url = "/api/integration/v1/daily-expenses/summary"
    backwards = {"de": "2026-10-10", "ate": "2026-10-01"}
    assert client.get(url, headers=bearer(token), params=backwards).status_code == 422
    too_long = {"de": "2026-01-01", "ate": "2026-04-04"}  # 94 dias
    assert client.get(url, headers=bearer(token), params=too_long).status_code == 422
    max_period = {"de": "2026-01-01", "ate": "2026-04-03"}  # 93 dias
    assert client.get(url, headers=bearer(token), params=max_period).status_code == 200


def test_period_summary_refuses_unknown_filters_and_ignores_empty_ones(client, db, users):
    token = issue_token(db, "user-a")
    add_daily(db, "user-a", THIS_MONTH, 100.0, "Supermercado", "Alimentação")
    url = "/api/integration/v1/daily-expenses/summary"
    period = {"de": THIS_MONTH.isoformat(), "ate": THIS_MONTH.isoformat()}
    for bad in ({"categoria": "Alimentacao"}, {"subcategoria": "Mercado"}):
        response = client.get(url, headers=bearer(token), params=period | bad)
        assert response.status_code == 422  # um total zero enganaria o Lumi
    empty = client.get(url, headers=bearer(token), params=period | {"categoria": "", "subcategoria": ""})
    assert empty.status_code == 200 and empty.json()["total"] == 100.0


def test_month_summary_has_both_free_balances(client, db, users):
    token = issue_token(db, "user-a")
    add_expense(db, "user-a", "Aluguel", 1500.0)
    add_expense(db, "user-a", "Internet", 120.0, status="Pago")
    db.add(
        Income(
            user_id="user-a",
            mes_referencia=THIS_MONTH,
            nome="Salário",
            valor=5000.0,
            data=THIS_MONTH,
            recorrente=True,
        )
    )
    db.commit()
    add_daily(db, "user-a", THIS_MONTH, 200.0, "Supermercado", "Alimentação")

    body = client.get(
        f"/api/integration/v1/months/{THIS_MONTH.year}/{THIS_MONTH.month}", headers=bearer(token)
    ).json()

    assert body["total_receitas"] == 5000.0
    assert body["total_despesas"] == 1620.0
    assert body["total_gastos_diarios"] == 200.0
    assert body["saldo_livre"] == 3380.0
    assert body["saldo_apos_diarios"] == 3180.0
    assert body["total_pago"] == 120.0 and body["total_pendente"] == 1500.0


def test_months_beyond_the_next_are_refused(client, db, users):
    token = issue_token(db, "user-a")
    later = add_months(THIS_MONTH, 2)
    nxt = add_months(THIS_MONTH, 1)
    for path in ("months", "expenses"):
        far = f"/api/integration/v1/{path}/{later.year}/{later.month}"
        assert client.get(far, headers=bearer(token)).status_code == 422
        near = f"/api/integration/v1/{path}/{nxt.year}/{nxt.month}"
        assert client.get(near, headers=bearer(token)).status_code == 200
    assert client.get("/api/integration/v1/months/2026/13", headers=bearer(token)).status_code == 422
    assert client.get("/api/integration/v1/expenses/1999/1", headers=bearer(token)).status_code == 422
    assert client.get("/api/integration/v1/months/10000/1", headers=bearer(token)).status_code == 422


def test_expenses_of_the_month_only_from_the_owner(client, db, users):
    token = issue_token(db, "user-a")
    add_expense(db, "user-a", "Energia elétrica", 230.0)
    add_expense(db, "user-b", "Aluguel do B", 900.0)

    body = client.get(
        f"/api/integration/v1/expenses/{THIS_MONTH.year}/{THIS_MONTH.month}", headers=bearer(token)
    ).json()

    assert [(e["nome"], e["valor"], e["status"]) for e in body] == [("Energia elétrica", 230.0, "Pendente")]
    assert set(body[0]) == {
        "id", "nome", "valor", "vencimento", "status", "categoria", "subcategoria",
        "parcela_atual", "parcela_total",
    }


def test_patch_changes_only_the_status_of_own_expenses(client, db, users):
    token = issue_token(db, "user-a")
    luz = add_expense(db, "user-a", "Energia elétrica", 230.0)
    alheia = add_expense(db, "user-b", "Aluguel do B", 900.0)
    url = f"/api/integration/v1/expenses/{luz}"

    paid = client.patch(url, headers=bearer(token), json={"status": "Pago"})
    assert paid.status_code == 200 and paid.json()["status"] == "Pago"
    back = client.patch(url, headers=bearer(token), json={"status": "Pendente"})
    assert back.json()["status"] == "Pendente"

    assert client.patch(url, headers=bearer(token), json={"status": "Atrasado"}).status_code == 422
    assert client.patch(url, headers=bearer(token), json={"status": "Pago", "valor": 1}).status_code == 422
    assert client.patch(url, headers=bearer(token), json={"valor": 1}).status_code == 422
    other = client.patch(
        f"/api/integration/v1/expenses/{alheia}", headers=bearer(token), json={"status": "Pago"}
    )
    assert other.status_code == 404
    db.expire_all()
    assert db.get(Expense, alheia).status == ExpenseStatus.PENDENTE.value
    assert float(db.get(Expense, luz).valor) == 230.0


def test_unpaying_an_overdue_expense_answers_atrasado(client, db, users):
    """Pendente com vencimento passado volta como Atrasado (RF-05): o que o app vai mostrar."""
    token = issue_token(db, "user-a")
    vencida = Expense(
        user_id="user-a",
        mes_referencia=THIS_MONTH,
        nome="Condomínio",
        valor=600.0,
        vencimento=TODAY - timedelta(days=1),
        recorrente=True,
        status=ExpenseStatus.PAGO.value,
    )
    db.add(vencida)
    db.commit()

    response = client.patch(
        f"/api/integration/v1/expenses/{vencida.id}", headers=bearer(token), json={"status": "Pendente"}
    )

    assert response.status_code == 200 and response.json()["status"] == "Atrasado"


def test_app_daily_expense_route_keeps_its_validation(client, db, users):
    """A rota do app usa a mesma validacao compartilhada com a integracao."""
    jwt = {"Authorization": f"Bearer {create_access_token({'sub': 'user-a', 'email': 'a@example.com'})}"}
    url = f"/api/daily-expenses/{THIS_MONTH.year}/{THIS_MONTH.month}"
    payload = {
        "descricao": "Café",
        "valor": 8.5,
        "data": THIS_MONTH.isoformat(),
        "subcategoria": "Café",
        "metodo_pagamento": "Pix",
    }
    created = client.post(url, headers=jwt, json=payload)
    assert created.status_code == 201 and created.json()["categoria"] == "Alimentação"
    bad = client.post(url, headers=jwt, json=payload | {"subcategoria": "Cafezinho"})
    assert bad.status_code == 422 and bad.json() == {"detail": "Subcategoria inválida: Cafezinho"}
    bad = client.post(url, headers=jwt, json=payload | {"metodo_pagamento": "Cheque"})
    assert bad.json() == {"detail": "Método de pagamento inválido: Cheque"}
