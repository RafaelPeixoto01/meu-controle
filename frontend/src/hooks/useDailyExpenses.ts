import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../services/api";
import type {
  DailyExpenseCreate,
  DailyExpenseUpdate,
  DailyExpenseMonthlySummary,
  CategoriesData,
} from "../types";

const DAILY_KEY = ["daily-expenses-summary"];
const CATEGORIES_KEY = ["daily-expenses-categories"];

export function useDailyExpensesMonthly(year: number, month: number) {
  return useQuery<DailyExpenseMonthlySummary>({
    queryKey: [...DAILY_KEY, year, month],
    queryFn: () => api.fetchDailyExpensesMonthly(year, month),
  });
}

export function useDailyExpensesCategories() {
  return useQuery<CategoriesData>({
    queryKey: CATEGORIES_KEY,
    queryFn: () => api.fetchDailyExpensesCategories(),
    staleTime: Infinity,
  });
}

export function useCreateDailyExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DailyExpenseCreate) =>
      api.createDailyExpense(year, month, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DAILY_KEY });
    },
  });
}

export function useUpdateDailyExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DailyExpenseUpdate }) =>
      api.updateDailyExpense(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DAILY_KEY });
    },
  });
}

export function useDeleteDailyExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteDailyExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DAILY_KEY });
    },
  });
}
