from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from typing import Generator

DATABASE_URL = "sqlite:///meu_controle.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Necessario para SQLite com FastAPI
)

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
