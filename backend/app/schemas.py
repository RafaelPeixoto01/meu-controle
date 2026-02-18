from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from typing import Optional

from app.models import ExpenseStatus


# ========== Expense Schemas ==========

class ExpenseCreate(BaseModel):
    """Schema para criacao de despesa. mes_referencia vem da URL, status padrao Pendente."""
    nome: str = Field(..., min_length=1, max_length=255)
    valor: float = Field(..., gt=0)
    vencimento: date
    parcela_atual: Optional[int] = Field(None, ge=1)
    parcela_total: Optional[int] = Field(None, ge=1)
    recorrente: bool = True

    @model_validator(mode="after")
    def validate_parcelas(self) -> "ExpenseCreate":
        """Regra de integridade do PRD: ambos os campos de parcela devem estar
        presentes ou ausentes, e parcela_atual <= parcela_total."""
        atual = self.parcela_atual
        total = self.parcela_total
        if (atual is None) != (total is None):
            raise ValueError(
                "parcela_atual e parcela_total devem ambos ser preenchidos ou ambos nulos"
            )
        if atual is not None and total is not None and atual > total:
            raise ValueError("parcela_atual deve ser <= parcela_total")
        return self


class ExpenseUpdate(BaseModel):
    """Schema para atualizacao parcial (PATCH). Apenas campos enviados sao alterados."""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    valor: Optional[float] = Field(None, gt=0)
    vencimento: Optional[date] = None
    parcela_atual: Optional[int] = Field(None, ge=1)
    parcela_total: Optional[int] = Field(None, ge=1)
    recorrente: Optional[bool] = None
    status: Optional[ExpenseStatus] = None


class ExpenseResponse(BaseModel):
    """Schema de resposta para despesa."""
    model_config = {"from_attributes": True}

    id: str
    mes_referencia: date
    nome: str
    valor: float
    vencimento: date
    parcela_atual: Optional[int]
    parcela_total: Optional[int]
    recorrente: bool
    status: str
    created_at: datetime
    updated_at: datetime


# ========== Income Schemas ==========

class IncomeCreate(BaseModel):
    """Schema para criacao de receita."""
    nome: str = Field(..., min_length=1, max_length=255)
    valor: float = Field(..., gt=0)
    data: Optional[date] = None
    recorrente: bool = True


class IncomeUpdate(BaseModel):
    """Schema para atualizacao parcial de receita."""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    valor: Optional[float] = Field(None, gt=0)
    data: Optional[date] = None
    recorrente: Optional[bool] = None


class IncomeResponse(BaseModel):
    """Schema de resposta para receita."""
    model_config = {"from_attributes": True}

    id: str
    mes_referencia: date
    nome: str
    valor: float
    data: Optional[date]
    recorrente: bool
    created_at: datetime
    updated_at: datetime


# ========== Summary Schema ==========

class MonthlySummary(BaseModel):
    """Resposta composta da visao mensal: despesas + receitas + totalizadores."""
    mes_referencia: date
    total_despesas: float
    total_receitas: float
    saldo_livre: float
    total_pago: float       # CR-004: total despesas com status Pago
    total_pendente: float   # CR-004: total despesas com status Pendente
    total_atrasado: float   # CR-004: total despesas com status Atrasado
    expenses: list[ExpenseResponse]
    incomes: list[IncomeResponse]


# ========== Daily Expense Schemas (CR-005) ==========

class DailyExpenseCreate(BaseModel):
    """Schema para criacao de gasto diario. mes_referencia derivado da URL."""
    descricao: str = Field(..., min_length=1, max_length=255)
    valor: float = Field(..., gt=0)
    data: date
    subcategoria: str = Field(..., min_length=1, max_length=50)
    metodo_pagamento: str = Field(..., min_length=1, max_length=30)


class DailyExpenseUpdate(BaseModel):
    """Schema para atualizacao parcial de gasto diario."""
    descricao: Optional[str] = Field(None, min_length=1, max_length=255)
    valor: Optional[float] = Field(None, gt=0)
    data: Optional[date] = None
    subcategoria: Optional[str] = Field(None, min_length=1, max_length=50)
    metodo_pagamento: Optional[str] = Field(None, min_length=1, max_length=30)


class DailyExpenseResponse(BaseModel):
    """Schema de resposta para gasto diario."""
    model_config = {"from_attributes": True}

    id: str
    mes_referencia: date
    descricao: str
    valor: float
    data: date
    categoria: str
    subcategoria: str
    metodo_pagamento: str
    created_at: datetime
    updated_at: datetime


class DailyExpenseDaySummary(BaseModel):
    """Gastos de um unico dia, agrupados."""
    data: date
    gastos: list[DailyExpenseResponse]
    subtotal: float


class DailyExpenseMonthlySummary(BaseModel):
    """Resposta da visao mensal de gastos diarios."""
    mes_referencia: date
    total_mes: float
    dias: list[DailyExpenseDaySummary]


class CategoriesResponse(BaseModel):
    """Resposta com categorias e metodos de pagamento disponiveis."""
    categorias: dict[str, list[str]]
    metodos_pagamento: list[str]


# ========== Auth Schemas (CR-002) ==========

class UserCreate(BaseModel):
    """Schema para cadastro de usuario."""
    nome: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema para atualizacao de perfil."""
    nome: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)


class UserResponse(BaseModel):
    """Schema de resposta para usuario."""
    model_config = {"from_attributes": True}

    id: str
    nome: str
    email: str
    avatar_url: Optional[str]
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Schema para login com email/senha."""
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    """Schema para login com Google OAuth2."""
    code: str


class RefreshTokenRequest(BaseModel):
    """Schema para refresh de token."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Schema de resposta com tokens JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class ForgotPasswordRequest(BaseModel):
    """Schema para solicitar reset de senha."""
    email: str


class ResetPasswordRequest(BaseModel):
    """Schema para redefinir senha."""
    token: str
    new_password: str = Field(..., min_length=6)


class ChangePasswordRequest(BaseModel):
    """Schema para trocar senha pelo perfil."""
    current_password: str
    new_password: str = Field(..., min_length=6)
