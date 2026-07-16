"""
CR-044: Testes de headers de segurança (CSP/HSTS) e rate limiting.
"""
import pytest
from starlette.testclient import TestClient

import app.main as main
from app.main import app
from app.database import get_db
from app.rate_limit import limiter


@pytest.fixture
def client():
    return TestClient(app)


# ---------- CSP / HSTS ----------

def test_csp_presente_em_todas_respostas(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    csp = r.headers.get("Content-Security-Policy")
    assert csp is not None
    # Diretivas-chave e exceções necessárias (CR-044 §3)
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "https://*.googleusercontent.com" in csp        # avatares Google
    assert "'unsafe-inline'" in csp                          # recharts
    assert "https://fonts.gstatic.com" in csp               # fonte Outfit


def test_headers_basicos_mantidos(client):
    r = client.get("/api/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_hsts_ausente_em_dev(client):
    """Em dev (ENVIRONMENT=development, default) o HSTS NÃO deve ser enviado."""
    assert main._IS_PRODUCTION is False
    r = client.get("/api/health")
    assert "Strict-Transport-Security" not in r.headers


# ---------- Rate limiting ----------

@pytest.fixture
def db_override():
    """Sobrescreve get_db com uma sessão SQLite in-memory vazia (login retorna 401)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base

    # StaticPool + check_same_thread: todas as sessões compartilham a MESMA
    # conexão in-memory (senão cada sessão veria um banco vazio próprio).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)

    def _override():
        s = TestingSession()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _override
    limiter.reset()  # zera contadores antes do teste
    yield
    app.dependency_overrides.pop(get_db, None)
    limiter.reset()


def test_login_bloqueia_apos_5_por_minuto(client, db_override):
    """5 tentativas passam (401 credenciais inválidas); a 6ª é bloqueada (429)."""
    payload = {"email": "nobody@example.com", "password": "wrong"}
    codes = [client.post("/api/auth/login", json=payload).status_code for _ in range(5)]
    assert all(c == 401 for c in codes), f"esperava 401 nas 5 primeiras, veio {codes}"

    blocked = client.post("/api/auth/login", json=payload)
    assert blocked.status_code == 429


def test_forgot_password_bloqueia_apos_3_por_minuto(client, db_override):
    """3 tentativas passam (200 genérico); a 4ª é bloqueada (429)."""
    payload = {"email": "nobody@example.com"}
    codes = [client.post("/api/auth/forgot-password", json=payload).status_code for _ in range(3)]
    assert all(c == 200 for c in codes), f"esperava 200 nas 3 primeiras, veio {codes}"

    blocked = client.post("/api/auth/forgot-password", json=payload)
    assert blocked.status_code == 429
