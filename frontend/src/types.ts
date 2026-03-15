// ========== Expense Types ==========

export type ExpenseStatus = "Pendente" | "Pago" | "Atrasado";

export interface Expense {
  id: string;
  mes_referencia: string;
  nome: string;
  categoria: string | null;  // CR-016
  subcategoria: string | null;  // CR-016
  valor: number;
  vencimento: string;
  parcela_atual: number | null;
  parcela_total: number | null;
  recorrente: boolean;
  status: ExpenseStatus;
  created_at: string;
  updated_at: string;
}

export interface ExpenseCreate {
  nome: string;
  valor: number;
  vencimento: string;
  parcela_atual?: number | null;
  parcela_total?: number | null;
  recorrente: boolean;
  subcategoria?: string | null;  // CR-016
}

export interface ExpenseUpdate {
  nome?: string;
  valor?: number;
  vencimento?: string;
  parcela_atual?: number | null;
  parcela_total?: number | null;
  recorrente?: boolean;
  status?: ExpenseStatus;
  subcategoria?: string | null;  // CR-016
}

export interface InstallmentGroup {
  nome: string;
  parcela_total: number;
  status_geral: string;
  valor_total_compra: number;
  valor_pago: number;
  valor_restante: number;
  installments: Expense[];
}

export interface InstallmentsResponse {
  groups: InstallmentGroup[];
  total_gasto: number;
  total_pago: number;
  total_pendente: number;
  total_atrasado: number;
}

// ========== Income Types ==========

export interface Income {
  id: string;
  mes_referencia: string;
  nome: string;
  valor: number;
  data: string | null;
  recorrente: boolean;
  created_at: string;
  updated_at: string;
}

export interface IncomeCreate {
  nome: string;
  valor: number;
  data?: string | null;
  recorrente: boolean;
}

export interface IncomeUpdate {
  nome?: string;
  valor?: number;
  data?: string | null;
  recorrente?: boolean;
}

// ========== Monthly Summary ==========

export interface MonthlySummary {
  mes_referencia: string;
  total_despesas: number;
  total_receitas: number;
  saldo_livre: number;
  total_pago: number;       // CR-004
  total_pendente: number;   // CR-004
  total_atrasado: number;   // CR-004
  expenses: Expense[];
  incomes: Income[];
}

// ========== Daily Expense Types (CR-005) ==========

export interface DailyExpense {
  id: string;
  mes_referencia: string;
  descricao: string;
  valor: number;
  data: string;
  categoria: string;
  subcategoria: string;
  metodo_pagamento: string;
  created_at: string;
  updated_at: string;
}

export interface DailyExpenseCreate {
  descricao: string;
  valor: number;
  data: string;
  subcategoria: string;
  metodo_pagamento: string;
}

export interface DailyExpenseUpdate {
  descricao?: string;
  valor?: number;
  data?: string;
  subcategoria?: string;
  metodo_pagamento?: string;
}

export interface DailyExpenseDaySummary {
  data: string;
  gastos: DailyExpense[];
  subtotal: number;
}

export interface DailyExpenseMonthlySummary {
  mes_referencia: string;
  total_mes: number;
  dias: DailyExpenseDaySummary[];
}

export interface CategoriesData {
  categorias: Record<string, string[]>;
  metodos_pagamento: string[];
}

// ========== Installment Projection Types (CR-021) ==========

export interface InstallmentProjectionItem {
  nome: string;
  valor_mensal: number;
  parcela_atual: number;
  parcela_total: number;
  parcelas_restantes: number;
  mes_termino: string | null;
  status_badge: "Encerrando" | "Ativa";
}

export interface MonthProjectionPoint {
  mes: string;
  total_comprometido: number;
  parcelas_ativas: number;
  parcelas_encerrando: string[];
  valor_liberado: number;
  percentual_comprometimento: number;
}

export interface ProximaEncerrar {
  nome: string;
  mes_termino: string;
}

export interface InstallmentProjectionResponse {
  total_comprometido_mes_atual: number;
  total_restante_todas_parcelas: number;
  qtd_parcelas_ativas: number;
  proxima_a_encerrar: ProximaEncerrar | null;
  liberacao_proximos_3_meses: number;
  percentual_renda_comprometida: number;
  renda_atual: number;
  projecao_mensal: MonthProjectionPoint[];
  parcelas: InstallmentProjectionItem[];
}

// ========== Dashboard Types (CR-019) ==========

export interface CategoryBreakdown {
  categoria: string;
  total: number;
  percentual: number;
  count: number;
}

export interface MonthEvolutionPoint {
  mes_referencia: string;
  total_despesas: number;
  total_receitas: number;
  total_gastos_diarios: number;
  saldo_livre: number;
}

export interface DashboardData {
  mes_referencia: string;
  total_receitas: number;
  total_despesas_planejadas: number;
  total_gastos_diarios: number;
  total_despesas_geral: number;
  saldo_livre: number;
  percentual_comprometimento: number;
  total_parcelas_futuras: number;
  total_pago: number;
  total_pendente: number;
  total_atrasado: number;
  categorias_planejadas: CategoryBreakdown[];
  categorias_diarios: CategoryBreakdown[];
  evolucao: MonthEvolutionPoint[];
}

// ========== Auth Types (CR-002) ==========

export interface User {
  id: string;
  nome: string;
  email: string;
  avatar_url: string | null;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;  // Enviado via HttpOnly cookie, pode estar ausente no body
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  nome: string;
  email: string;
  password: string;
}

export interface TokenResponse extends AuthTokens {
  user?: User;
}
