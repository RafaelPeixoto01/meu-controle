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
      queryClient.invalidateQueries({ queryKey: ["installments"] });
    },
  });
}

export function useUpdateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ExpenseUpdate }) =>
      api.updateExpense(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
      queryClient.invalidateQueries({ queryKey: ["installments"] });
    },
  });
}

export function useDeleteExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, deleteAll }: { id: string; deleteAll?: boolean }) =>
      api.deleteExpense(id, deleteAll),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
      queryClient.invalidateQueries({ queryKey: ["installments"] });
    },
  });
}

export function useDuplicateExpense() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.duplicateExpense(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
      queryClient.invalidateQueries({ queryKey: ["installments"] });
    },
  });
}
