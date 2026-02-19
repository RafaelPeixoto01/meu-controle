// ========== Expense Types ==========

export type ExpenseStatus = "Pendente" | "Pago" | "Atrasado";

export interface Expense {
  id: string;
  mes_referencia: string;
  nome: string;
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
}

export interface ExpenseUpdate {
  nome?: string;
  valor?: number;
  vencimento?: string;
  parcela_atual?: number | null;
  parcela_total?: number | null;
  recorrente?: boolean;
  status?: ExpenseStatus;
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
  refresh_token: string;
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
