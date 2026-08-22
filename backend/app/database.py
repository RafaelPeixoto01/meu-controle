import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///meu_controle.db")

# Railway PostgreSQL usa "postgres://" mas SQLAlchemy exige "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency injection: fornece sessao do banco e garante cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_factory() -> sessionmaker:
    """
    CR-052: factory de sessao para trabalho fora do request (BackgroundTasks).

    A sessao injetada por `get_db` ja foi fechada quando a task roda, entao a
    task precisa abrir a sua propria. Exposto como dependency (e nao usando
    `SessionLocal` direto) para que os testes o sobrescrevam via
    `app.dependency_overrides`, o mesmo mecanismo ja usado com `get_db`.
    """
    return SessionLocal
