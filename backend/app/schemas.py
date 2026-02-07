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
    expenses: list[ExpenseResponse]
    incomes: list[IncomeResponse]
