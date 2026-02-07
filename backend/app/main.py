from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import expenses, incomes, months


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: criar todas as tabelas
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: nada a limpar para SQLite


app = FastAPI(
    title="Meu Controle API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(months.router)
app.include_router(expenses.router)
app.include_router(incomes.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
