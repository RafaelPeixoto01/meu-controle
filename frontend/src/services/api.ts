import type {
  MonthlySummary,
  ExpenseCreate,
  ExpenseUpdate,
  Expense,
  IncomeCreate,
  IncomeUpdate,
  Income,
} from "../types";

const BASE_URL = "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
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

export function deleteExpense(id: string): Promise<void> {
  return request<void>(`/expenses/${id}`, { method: "DELETE" });
}

export function duplicateExpense(id: string): Promise<Expense> {
  return request<Expense>(`/expenses/${id}/duplicate`, { method: "POST" });
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
