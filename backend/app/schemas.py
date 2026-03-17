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
    subcategoria: Optional[str] = Field(None, max_length=50)  # CR-016

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
    subcategoria: Optional[str] = Field(None, max_length=50)  # CR-016


class ExpenseResponse(BaseModel):
    """Schema de resposta para despesa."""
    model_config = {"from_attributes": True}

    id: str
    mes_referencia: date
    nome: str
    categoria: Optional[str] = None  # CR-016
    subcategoria: Optional[str] = None  # CR-016
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
    """Schema de resposta com tokens JWT. refresh_token enviado via HttpOnly cookie, nao no body."""
    access_token: str
    refresh_token: Optional[str] = None
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


# ========== Installments Schemas (CR-007) ==========

class InstallmentGroup(BaseModel):
    """Grupo de parcelas de uma mesma compra."""
    nome: str
    parcela_total: int
    status_geral: str
    valor_total_compra: float
    valor_pago: float
    valor_restante: float
    installments: list[ExpenseResponse]


class InstallmentsResponse(BaseModel):
    """Resposta consolidada de parcelamentos."""
    groups: list[InstallmentGroup]
    total_gasto: float
    total_pago: float
    total_pendente: float
    total_atrasado: float


# ========== Installment Projection Schemas (CR-021) ==========

class InstallmentProjectionItem(BaseModel):
    """Info de uma parcela ativa para projecao e tabela aprimorada."""
    nome: str
    valor_mensal: float
    parcela_atual: int
    parcela_total: int
    parcelas_restantes: int
    mes_inicio: Optional[date] = None
    mes_termino: Optional[date] = None
    status_badge: str  # "Encerrando" | "Ativa"


class MonthProjectionPoint(BaseModel):
    """Ponto de projecao mensal para grafico de barras empilhadas."""
    mes: date
    total_comprometido: float
    parcelas_ativas: int
    parcelas_encerrando: list[str]
    valor_liberado: float
    percentual_comprometimento: float


class ProximaEncerrar(BaseModel):
    """Info da proxima parcela a encerrar."""
    nome: str
    mes_termino: date


class InstallmentProjectionResponse(BaseModel):
    """Resposta completa da projecao de parcelas (CR-021)."""
    # Summary KPIs (6 cards)
    total_comprometido_mes_atual: float
    total_restante_todas_parcelas: float
    qtd_parcelas_ativas: int
    proxima_a_encerrar: Optional[ProximaEncerrar] = None
    liberacao_proximos_3_meses: float
    percentual_renda_comprometida: float
    renda_atual: float
    # Projecao mensal (12 meses)
    projecao_mensal: list[MonthProjectionPoint]
    # Parcelas para tabela e gantt
    parcelas: list[InstallmentProjectionItem]


# ========== Dashboard Schemas (CR-019) ==========

class CategoryBreakdown(BaseModel):
    """Breakdown de despesas por categoria para graficos donut."""
    categoria: str
    total: float
    percentual: float
    count: int


class MonthEvolutionPoint(BaseModel):
    """Ponto de dados para grafico de evolucao mensal (6 meses)."""
    mes_referencia: date
    total_despesas: float
    total_receitas: float
    total_gastos_diarios: float
    saldo_livre: float


class DashboardResponse(BaseModel):
    """Resposta completa do dashboard para um mes."""
    mes_referencia: date
    # Indicadores-chave
    total_receitas: float
    total_despesas_planejadas: float
    total_gastos_diarios: float
    total_despesas_geral: float
    saldo_livre: float
    percentual_comprometimento: float
    total_parcelas_futuras: float
    # Status breakdown (apenas planejadas)
    total_pago: float
    total_pendente: float
    total_atrasado: float
    # Composicao por categoria — separados
    categorias_planejadas: list[CategoryBreakdown]
    categorias_diarios: list[CategoryBreakdown]
    # Evolucao 6 meses
    evolucao: list[MonthEvolutionPoint]


# ========== Health Score (CR-026) ==========

class D2SubfactorDetail(BaseModel):
    pontos: int
    valor: float | int | None = None
    quantidade: int | None = None
    percentual_liberacao: float | None = None

class D4SubfactorDetail(BaseModel):
    pontos: int
    percentual_em_dia: float | None = None
    dias_registro: int | None = None
    primeiro_mes: bool | None = None
    nova_parcela_longa: str | None = None

class D2SubfactorsGroup(BaseModel):
    d2a_percentual: D2SubfactorDetail
    d2b_quantidade: D2SubfactorDetail
    d2c_pendentes: D2SubfactorDetail
    d2d_alivio: D2SubfactorDetail

class D4SubfactorsGroup(BaseModel):
    d4a_pontualidade: D4SubfactorDetail
    d4b_consistencia: D4SubfactorDetail
    d4c_tendencia: D4SubfactorDetail
    d4d_disciplina: D4SubfactorDetail

class ScoreDimensionD1(BaseModel):
    pontos: int
    maximo: int
    percentual_comprometimento: float
    detalhe: str

class ScoreDimensionD2(BaseModel):
    pontos: int
    maximo: int
    subfatores: D2SubfactorsGroup | dict = {}
    detalhe: str

class ScoreDimensionD3(BaseModel):
    pontos: int
    maximo: int
    percentual_livre: float
    estimativa_variaveis: bool
    dias_dados_variaveis: int
    detalhe: str

class ScoreDimensionD4(BaseModel):
    pontos: int
    maximo: int
    subfatores: D4SubfactorsGroup | dict = {}
    detalhe: str

class ScoreDimensoes(BaseModel):
    d1_comprometimento: ScoreDimensionD1
    d2_parcelas: ScoreDimensionD2
    d3_poupanca: ScoreDimensionD3
    d4_comportamento: ScoreDimensionD4

class ScoreInfo(BaseModel):
    total: int
    classificacao: str
    cor: str
    mensagem: str
    mensagem_contextual: str
    variacao_mes_anterior: int | None = None
    mes_referencia: str

class ConservativePendingItem(BaseModel):
    descricao: str
    valor_estimado_mensal: float
    total_parcelas: int

class ConservativeScenario(BaseModel):
    score: int
    classificacao: str
    parcelas_pendentes: list[ConservativePendingItem]
    impacto: str

class ScoreAction(BaseModel):
    prioridade: int
    dimensao_alvo: str
    descricao: str
    impacto_estimado: int
    tipo: str

class HealthScoreResponse(BaseModel):
    score: ScoreInfo
    dimensoes: ScoreDimensoes
    cenario_conservador: ConservativeScenario | None = None
    acoes: list[ScoreAction] = []

class ScoreHistoryItem(BaseModel):
    mes_referencia: str
    score_total: int
    classificacao: str
    d1: int
    d2: int
    d3: int
    d4: int

class ScoreHistoryResponse(BaseModel):
    historico: list[ScoreHistoryItem]
    meses_solicitados: int
    meses_disponiveis: int


# ========== AI Analysis (CR-032) ==========

class AiCategoriaDestaque(BaseModel):
    categoria: str
    percentual_renda: float
    benchmark_saudavel: float
    variacao_mensal_percentual: float
    observacao: str


class AiDiagnostico(BaseModel):
    resumo_geral: str
    comparativo_benchmark: str
    variacao_vs_mes_anterior: str | None = None
    categorias_destaque: list[AiCategoriaDestaque] = []


class AiAlerta(BaseModel):
    tipo: str  # critico | atencao | informativo
    titulo: str
    descricao: str
    impacto_mensal: float
    impacto_anual: float


class AiBomComportamento(BaseModel):
    comportamento: str
    mensagem_reforco: str


class AiRecomendacao(BaseModel):
    prioridade: int
    acao: str
    justificativa: str
    economia_estimada_mensal: float
    dificuldade: str  # fácil | moderada | difícil
    impacto_score_estimado: int


class AiMeta(BaseModel):
    descricao: str
    valor_alvo: float
    prazo_meses: int
    primeiro_passo: str


class AiMetas(BaseModel):
    curto_prazo: AiMeta
    medio_prazo: AiMeta
    longo_prazo: AiMeta


class AiGastoRecorrente(BaseModel):
    descricao: str
    frequencia_mensal: int
    valor_medio_mensal: float
    sugestao: str


class AiAnalysisResult(BaseModel):
    diagnostico: AiDiagnostico
    alertas: list[AiAlerta] = []
    bons_comportamentos: list[AiBomComportamento] = []
    recomendacoes: list[AiRecomendacao] = []
    metas: AiMetas
    gastos_recorrentes_disfarcados: list[AiGastoRecorrente] = []
    mensagem_motivacional: str


class AiAnalysisResponse(BaseModel):
    status: str  # disponivel | indisponivel | erro
    mes_referencia: str | None = None
    score_referencia: int | None = None
    resultado: AiAnalysisResult | None = None
    modelo: str | None = None
    generated_at: str | None = None
    is_cached: bool = False
    reason: str | None = None
