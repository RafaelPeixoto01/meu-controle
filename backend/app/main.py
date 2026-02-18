import logging
from pathlib import Path
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import expenses, incomes, months, auth, users, daily_expenses  # CR-002: auth, users; CR-005: daily_expenses


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: migrations gerenciadas pelo Alembic (ver CR-001)
    yield


app = FastAPI(
    title="Meu Controle API",
    version="2.0.0",  # CR-002
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)    # CR-002: autenticacao (register, login, Google, refresh, logout, forgot/reset password)
app.include_router(users.router)   # CR-002: perfil de usuario (GET/PATCH /me, change password)
app.include_router(months.router)
app.include_router(expenses.router)
app.include_router(incomes.router)
app.include_router(daily_expenses.router)  # CR-005: gastos diarios


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
