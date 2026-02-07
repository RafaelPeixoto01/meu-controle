import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../services/api";
import type { ExpenseCreate, ExpenseUpdate } from "../types";

const MONTHLY_KEY = ["monthly-summary"];

export function useCreateExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ExpenseCreate) => api.createExpense(year, month, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
    },
  });
}

export function useUpdateExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ExpenseUpdate }) =>
      api.updateExpense(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
    },
  });
}

export function useDeleteExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
    },
  });
}

export function useDuplicateExpense(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.duplicateExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
    },
  });
}
