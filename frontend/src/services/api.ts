import type {
  MonthlySummary,
  ExpenseCreate,
  ExpenseUpdate,
  Expense,
  IncomeCreate,
  IncomeUpdate,
  Income,
  DailyExpenseMonthlySummary,
  DailyExpenseCreate,
  DailyExpenseUpdate,
  DailyExpense,
  CategoriesData,
  InstallmentsResponse,
} from "../types";

const BASE_URL = "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  // CR-002: incluir token de auth se disponivel
  const token = localStorage.getItem("access_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${url}`, {
    headers,
    ...options,
  });

  // CR-002: interceptar 401 para tentar refresh
  if (response.status === 401 && token) {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      try {
        const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (refreshResponse.ok) {
          const tokens = await refreshResponse.json();
          localStorage.setItem("access_token", tokens.access_token);
          localStorage.setItem("refresh_token", tokens.refresh_token);
          // Retry original request com novo token
          headers["Authorization"] = `Bearer ${tokens.access_token}`;
          const retryResponse = await fetch(`${BASE_URL}${url}`, {
            headers,
            ...options,
          });
          if (!retryResponse.ok) {
            const error = await retryResponse.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${retryResponse.status}`);
          }
          if (retryResponse.status === 204) return undefined as T;
          return retryResponse.json();
        }
      } catch {
        // Refresh falhou — limpar tokens e redirecionar
      }
    }
    // Refresh token invalido ou ausente
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
    throw new Error("Sessao expirada");
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

// ========== Monthly ==========

export function fetchMonthlySummary(
  year: number,
  month: number
): Promise<MonthlySummary> {
  return request<MonthlySummary>(`/months/${year}/${month}`);
}

// ========== Expenses ==========

export function createExpense(
  year: number,
  month: number,
  data: ExpenseCreate
): Promise<Expense> {
  return request<Expense>(`/expenses/${year}/${month}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateExpense(
  id: string,
  data: ExpenseUpdate
): Promise<Expense> {
  return request<Expense>(`/expenses/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteExpense(id: string, deleteAll: boolean = false): Promise<void> {
  const url = deleteAll ? `/expenses/${id}?delete_all=true` : `/expenses/${id}`;
  return request<void>(url, { method: "DELETE" });
}

export function duplicateExpense(id: string): Promise<Expense> {
  return request<Expense>(`/expenses/${id}/duplicate`, { method: "POST" });
}

export function fetchInstallments(): Promise<InstallmentsResponse> {
  return request<InstallmentsResponse>("/expenses/installments");
}

// ========== Incomes ==========

export function createIncome(
  year: number,
  month: number,
  data: IncomeCreate
): Promise<Income> {
  return request<Income>(`/incomes/${year}/${month}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateIncome(
  id: string,
  data: IncomeUpdate
): Promise<Income> {
  return request<Income>(`/incomes/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteIncome(id: string): Promise<void> {
  return request<void>(`/incomes/${id}`, { method: "DELETE" });
}

// ========== Daily Expenses (CR-005) ==========

export function fetchDailyExpensesCategories(): Promise<CategoriesData> {
  return request<CategoriesData>("/daily-expenses/categories");
}

export function fetchDailyExpensesMonthly(
  year: number,
  month: number
): Promise<DailyExpenseMonthlySummary> {
  return request<DailyExpenseMonthlySummary>(
    `/daily-expenses/${year}/${month}`
  );
}

export function createDailyExpense(
  year: number,
  month: number,
  data: DailyExpenseCreate
): Promise<DailyExpense> {
  return request<DailyExpense>(`/daily-expenses/${year}/${month}`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateDailyExpense(
  id: string,
  data: DailyExpenseUpdate
): Promise<DailyExpense> {
  return request<DailyExpense>(`/daily-expenses/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteDailyExpense(id: string): Promise<void> {
  return request<void>(`/daily-expenses/${id}`, { method: "DELETE" });
}
