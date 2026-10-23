"""CR-058: gestao dos tokens de integracao do Lumi no Perfil (RF-22, RN-054)."""
import hashlib

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.auth import get_current_user
from app.database import Base, get_db
from app.main import app
from app.models import IntegrationToken, User
from app.rate_limit import limiter


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
def as_user(session_factory, users):
    """Devolve um TestClient autenticado (JWT do app) como o usuario escolhido."""
    limiter.reset()

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    def client_for(user: User) -> TestClient:
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app)

    yield client_for
    app.dependency_overrides.clear()


def stored_tokens(session_factory) -> list[IntegrationToken]:
    db = session_factory()
    try:
        return list(db.scalars(select(IntegrationToken)).all())
    finally:
        db.close()


def test_create_shows_the_token_once_and_stores_only_the_hash(as_user, users, session_factory):
    client = as_user(users[0])

    response = client.post("/api/integration-tokens", json={"name": "  Lumi da mesa  "})

    assert response.status_code == 201
    body = response.json()
    token = body["token"]
    assert token.startswith("mc_") and len(token) == 3 + 43
    assert body["name"] == "Lumi da mesa"
    assert body["prefix"] == token[3:11]
    assert body["last_used_at"] is None
    [row] = stored_tokens(session_factory)
    assert row.token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert row.user_id == "user-a"
    assert token not in (row.token_hash, row.prefix, row.name)


def test_default_name_and_invalid_names(as_user, users):
    client = as_user(users[0])
    assert client.post("/api/integration-tokens", json={}).json()["name"] == "Lumi"
    assert client.post("/api/integration-tokens", json={"name": "   "}).status_code == 422
    assert client.post("/api/integration-tokens", json={"name": "x" * 41}).status_code == 422


def test_list_shows_only_active_tokens_without_the_token(as_user, users):
    client = as_user(users[0])
    first = client.post("/api/integration-tokens", json={"name": "Primeiro"}).json()
    second = client.post("/api/integration-tokens", json={"name": "Segundo"}).json()
    assert client.delete(f"/api/integration-tokens/{first['id']}").status_code == 204

    listed = client.get("/api/integration-tokens").json()

    assert [t["id"] for t in listed] == [second["id"]]
    assert "token" not in listed[0] and "token_hash" not in listed[0]


def test_revoke_only_own_active_tokens(as_user, users, session_factory):
    token_id = as_user(users[0]).post("/api/integration-tokens", json={}).json()["id"]

    assert as_user(users[1]).delete(f"/api/integration-tokens/{token_id}").status_code == 404
    client_a = as_user(users[0])
    assert client_a.delete(f"/api/integration-tokens/{token_id}").status_code == 204
    assert client_a.delete(f"/api/integration-tokens/{token_id}").status_code == 404
    [row] = stored_tokens(session_factory)
    assert row.revoked_at is not None
    assert as_user(users[1]).get("/api/integration-tokens").json() == []


def test_limit_of_five_active_tokens(as_user, users):
    client = as_user(users[0])
    created = [client.post("/api/integration-tokens", json={}).json() for _ in range(5)]

    sixth = client.post("/api/integration-tokens", json={})
    assert sixth.status_code == 409
    assert sixth.json() == {"detail": "Limite de 5 tokens ativos"}

    client.delete(f"/api/integration-tokens/{created[0]['id']}")  # revogado nao conta
    assert client.post("/api/integration-tokens", json={}).status_code == 201


def test_requires_login():
    app.dependency_overrides.clear()
    client = TestClient(app)
    assert client.get("/api/integration-tokens").status_code == 401
    assert client.post("/api/integration-tokens", json={}).status_code == 401
