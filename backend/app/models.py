import uuid
import enum
from datetime import date, datetime

from sqlalchemy import String, Date, Boolean, Integer, Numeric, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseStatus(str, enum.Enum):
    PENDENTE = "Pendente"
    PAGO = "Pago"
    ATRASADO = "Atrasado"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Nullable para Google-only users
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    incomes = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    daily_expenses = relationship("DailyExpense", back_populates="user", cascade="all, delete-orphan")  # CR-005
    score_historico = relationship("ScoreHistorico", back_populates="user", cascade="all, delete-orphan")  # CR-026
    analises_financeiras = relationship("AnaliseFinanceira", back_populates="user", cascade="all, delete-orphan")  # CR-032
    alertas = relationship("AlertaEstado", back_populates="user", cascade="all, delete-orphan")  # CR-033
    configuracao_alertas = relationship("ConfiguracaoAlertas", back_populates="user", uselist=False, cascade="all, delete-orphan")  # CR-033


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        Index("ix_expenses_user_month", "user_id", "mes_referencia"),  # CR-002: indice composto
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # CR-002: FK para isolamento de dados (RN-015)
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(50), nullable=True)  # CR-016
    subcategoria: Mapped[str | None] = mapped_column(String(50), nullable=True)  # CR-016
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    parcela_atual: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parcela_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorrente: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    origem_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )  # ID da despesa de origem na replicacao (RF-06)
    status: Mapped[str] = mapped_column(
        String(20), default=ExpenseStatus.PENDENTE.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    user = relationship("User", back_populates="expenses")  # CR-002


class Income(Base):
    __tablename__ = "incomes"
    __table_args__ = (
        Index("ix_incomes_user_month", "user_id", "mes_referencia"),  # CR-002: indice composto
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )  # CR-002: FK para isolamento de dados (RN-015)
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    data: Mapped[date | None] = mapped_column(Date, nullable=True)
    recorrente: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    origem_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )  # ID da receita de origem na replicacao (RF-06)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    user = relationship("User", back_populates="incomes")  # CR-002


class DailyExpense(Base):
    """CR-005: Gastos diários não planejados."""
    __tablename__ = "daily_expenses"
    __table_args__ = (
        Index("ix_daily_expenses_user_month", "user_id", "mes_referencia"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategoria: Mapped[str] = mapped_column(String(50), nullable=False)
    metodo_pagamento: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now, onupdate=datetime.now
    )

    user = relationship("User", back_populates="daily_expenses")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user = relationship("User", back_populates="refresh_tokens")


class ScoreHistorico(Base):
    """CR-026: Histórico mensal do score de saúde financeira."""
    __tablename__ = "score_historico"
    __table_args__ = (
        UniqueConstraint("user_id", "mes_referencia", name="uq_score_user_month"),
        Index("ix_score_historico_user_month", "user_id", "mes_referencia"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    score_total: Mapped[int] = mapped_column(Integer, nullable=False)
    d1_comprometimento: Mapped[int] = mapped_column(Integer, nullable=False)
    d2_parcelas: Mapped[int] = mapped_column(Integer, nullable=False)
    d3_poupanca: Mapped[int] = mapped_column(Integer, nullable=False)
    d4_comportamento: Mapped[int] = mapped_column(Integer, nullable=False)
    classificacao: Mapped[str] = mapped_column(String(20), nullable=False)
    score_conservador: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dados_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user = relationship("User", back_populates="score_historico")


class AnaliseFinanceira(Base):
    """CR-032: Persistencia de analises financeiras geradas por IA."""
    __tablename__ = "analise_financeira"
    __table_args__ = (
        UniqueConstraint("user_id", "mes_referencia", "tipo", name="uq_analise_user_month_tipo"),
        Index("ix_analise_user_month", "user_id", "mes_referencia"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="mensal")
    score_referencia: Mapped[int] = mapped_column(Integer, nullable=False)
    dados_input: Mapped[str] = mapped_column(Text, nullable=False)
    resultado: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    modelo: Mapped[str] = mapped_column(String(50), nullable=False)
    tempo_processamento_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user = relationship("User", back_populates="analises_financeiras")


class AlertaEstado(Base):
    """CR-033: Estado persistido dos alertas inteligentes."""
    __tablename__ = "alerta_estado"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "alerta_tipo", "alerta_referencia", "mes_referencia",
            name="uq_alerta_user_tipo_ref_mes",
        ),
        Index("ix_alerta_user_status", "user_id", "status"),
        Index("ix_alerta_user_mes", "user_id", "mes_referencia"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    alerta_tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    alerta_referencia: Mapped[str] = mapped_column(String(100), nullable=False)
    mes_referencia: Mapped[date] = mapped_column(Date, nullable=False)
    severidade: Mapped[str] = mapped_column(String(20), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dados_extra: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ativo", nullable=False)
    contexto_aba: Mapped[str] = mapped_column(String(30), nullable=False)
    acao_tipo: Mapped[str | None] = mapped_column(String(30), nullable=True)
    acao_referencia_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    acao_destino: Mapped[str | None] = mapped_column(String(100), nullable=True)
    impacto_mensal: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    impacto_anual: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    visto_em: Mapped[datetime | None] = mapped_column(nullable=True)
    dispensado_em: Mapped[datetime | None] = mapped_column(nullable=True)
    resolvido_em: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    user = relationship("User", back_populates="alertas")


class ConfiguracaoAlertas(Base):
    """CR-033: Configurações de alertas por usuário."""
    __tablename__ = "configuracao_alertas"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    antecedencia_vencimento: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    alerta_atrasadas: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    alerta_parcelas_encerrando: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    alerta_score: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    alerta_comprometimento: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    limiar_comprometimento: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    alerta_parcela_ativada: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    alerta_ia: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="configuracao_alertas")
