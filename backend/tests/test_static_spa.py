"""
CR-043: Testes de regressao para o fallback do SPA (path traversal).

Cobre:
- O helper resolve_static_file (contencao de path).
- O comportamento HTTP real via TestClient, incluindo payloads percent-encoded
  ('..%2f', '%2e%2e%2f') que o Starlette entrega ja decodificados ao handler.
"""
import tempfile
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.responses import FileResponse
from starlette.testclient import TestClient

from app.main import resolve_static_file


@pytest.fixture
def static_env():
    """Cria uma arvore <root>/static (STATIC_DIR) e um segredo em <root>/secret.env."""
    root = Path(tempfile.mkdtemp())
    static = root / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("INDEX", encoding="utf-8")
    (static / "assets" / "app.js").write_text("APPJS", encoding="utf-8")
    (root / "secret.env").write_text("SECRET_KEY=supersecret123", encoding="utf-8")
    yield static
    # tmpdir e efemero; sem cleanup explicito necessario para o teste


@pytest.fixture
def client(static_env):
    """App que replica o handler serve_spa usando o helper REAL de app.main."""
    app = FastAPI()

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = resolve_static_file(static_env, full_path)
        if file_path is not None:
            return FileResponse(file_path)
        return FileResponse(static_env / "index.html")

    return TestClient(app)


# ---------- Helper (unidade) ----------

def test_helper_serve_arquivo_legitimo(static_env):
    assert resolve_static_file(static_env, "index.html") == (static_env / "index.html").resolve()
    assert resolve_static_file(static_env, "assets/app.js") == (static_env / "assets" / "app.js").resolve()


def test_helper_bloqueia_traversal(static_env):
    # Simula full_path ja decodificado (como o Starlette entrega apos %2f)
    assert resolve_static_file(static_env, "../secret.env") is None
    assert resolve_static_file(static_env, "../../etc/passwd") is None


def test_helper_arquivo_inexistente_retorna_none(static_env):
    assert resolve_static_file(static_env, "rota/de/spa") is None


# ---------- Handler (integracao HTTP) ----------

def test_rota_raiz_serve_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.text == "INDEX"


def test_arquivo_estatico_legitimo(client):
    r = client.get("/assets/app.js")
    assert r.status_code == 200
    assert r.text == "APPJS"


def test_rota_de_spa_cai_no_index(client):
    r = client.get("/dashboard/2026/7")
    assert r.status_code == 200
    assert r.text == "INDEX"


@pytest.mark.parametrize("payload", [
    "/..%2fsecret.env",       # ../secret.env percent-encoded
    "/%2e%2e%2fsecret.env",   # %2e%2e%2f -> ../secret.env
    "/assets/..%2f..%2fsecret.env",
])
def test_path_traversal_encoded_nao_vaza(client, payload):
    """Payloads que antes vazavam o arquivo agora caem no fallback index.html."""
    r = client.get(payload)
    assert r.status_code == 200
    assert "SECRET_KEY" not in r.text
    assert r.text == "INDEX"
