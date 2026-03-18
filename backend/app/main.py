import logging
import os
from pathlib import Path
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers import expenses, incomes, months, auth, users, daily_expenses, dashboard, score, ai_analysis, alerts  # CR-002: auth, users; CR-005: daily_expenses; CR-019: dashboard; CR-026: score; CR-032: ai_analysis; CR-033: alerts


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adiciona headers de segurança HTTP em todas as respostas."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validar variáveis de ambiente obrigatórias
    optional_with_warning = {
        "GOOGLE_CLIENT_ID": "Login com Google desabilitado",
        "SENDGRID_API_KEY": "Recuperação de senha por email desabilitada",
        "ANTHROPIC_API_KEY": "Análise financeira por IA desabilitada",  # CR-032
    }
    for var, warning in optional_with_warning.items():
        if not os.environ.get(var):
            logging.warning("Variável de ambiente %s não definida: %s", var, warning)
    yield


app = FastAPI(
    title="Meu Controle API",
    version="2.0.0",  # CR-002
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)

_ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)    # CR-002: autenticacao (register, login, Google, refresh, logout, forgot/reset password)
app.include_router(users.router)   # CR-002: perfil de usuario (GET/PATCH /me, change password)
app.include_router(months.router)
app.include_router(expenses.router)
app.include_router(incomes.router)
app.include_router(daily_expenses.router)  # CR-005: gastos diarios
app.include_router(dashboard.router)       # CR-019: dashboard visual
app.include_router(score.router)           # CR-026: score de saude financeira
app.include_router(ai_analysis.router)    # CR-032: analise financeira por IA
app.include_router(alerts.router)         # CR-033: alertas inteligentes


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/config")
def get_public_config():
    """Return public configuration (no secrets)."""
    import os
    return {
        "google_client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
    }


# Serve frontend static files in production
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve index.html for all non-API routes (SPA fallback)."""
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
