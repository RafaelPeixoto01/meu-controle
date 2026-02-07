import { useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../services/api";
import type { IncomeCreate, IncomeUpdate } from "../types";

const MONTHLY_KEY = ["monthly-summary"];

export function useCreateIncome(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: IncomeCreate) => api.createIncome(year, month, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
    },
  });
}

export function useUpdateIncome(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: IncomeUpdate }) =>
      api.updateIncome(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
    },
  });
}

export function useDeleteIncome(year: number, month: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.deleteIncome(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MONTHLY_KEY });
    },
  });
}
