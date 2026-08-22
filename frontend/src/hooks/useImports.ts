// CR-047 (F07): hooks TanStack Query da importacao de extratos/faturas.
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../services/api";
import type {
  Expense,
  ImportBatch,
  ImportBatchSummary,
  ImportConfirmRequest,
} from "../types";
import { useAuth } from "./useAuth";
import { monthsToFetchForMatches } from "../utils/importReview";

const PENDING_KEY = ["imports-pending"];

export function usePendingImports() {
  const { user } = useAuth();
  return useQuery<ImportBatchSummary[]>({
    queryKey: [...PENDING_KEY, user?.id],
    queryFn: () => api.fetchPendingImports(),
    enabled: !!user,
  });
}

// Mapa expense_id -> Expense dos meses relevantes as conciliacoes do lote,
// para exibir nome/valor do gasto planejado alvo na revisao.
export function useMatchTargets(batch: ImportBatch | null) {
  const { user } = useAuth();
  return useQuery<Record<string, Expense>>({
    queryKey: ["import-match-targets", user?.id, batch?.id],
    queryFn: async () => {
      const months = monthsToFetchForMatches(batch!);
      const summaries = await Promise.all(
        months.map(({ year, month }) =>
          api.fetchMonthlySummary(year, month).catch(() => null)
        )
      );
      const map: Record<string, Expense> = {};
      for (const summary of summaries) {
        for (const expense of summary?.expenses ?? []) {
          map[expense.id] = expense;
        }
      }
      return map;
    },
    enabled: !!user && !!batch,
  });
}

// CR-052: canal de polling do processamento assincrono. Reconsulta a cada 3s
// enquanto o lote esta em 'processando' e para sozinho em qualquer estado
// terminal — RN-048 garante que 'processando' nao dura para sempre.
const POLL_INTERVAL_MS = 3000;

export function useImportBatch(batchId: string | null, enabled: boolean) {
  const { user } = useAuth();
  return useQuery<ImportBatch>({
    queryKey: ["import-batch", user?.id, batchId],
    queryFn: () => api.fetchImportBatch(batchId!),
    enabled: !!user && !!batchId && enabled,
    staleTime: 0, // sobrescreve o default de 5 min do queryClient
    // Com staleTime 0, o refetch por foco traria um objeto novo e resetaria as
    // edicoes em andamento na revisao; o polling ja cobre a atualizacao
    refetchOnWindowFocus: false,
    refetchInterval: (query) =>
      query.state.data?.status === "processando" ? POLL_INTERVAL_MS : false,
  });
}

export function useUploadImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.uploadImport(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PENDING_KEY });
    },
  });
}

export function useConfirmImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ batchId, data }: { batchId: string; data: ImportConfirmRequest }) =>
      api.confirmImport(batchId, data),
    onSuccess: () => {
      // Confirmacao cria gastos diarios e atualiza planejados — invalida tudo que agrega
      queryClient.invalidateQueries({ queryKey: PENDING_KEY });
      queryClient.invalidateQueries({ queryKey: ["daily-expenses-summary"] });
      queryClient.invalidateQueries({ queryKey: ["monthly-summary"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["installments"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });
}

export function useDiscardImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (batchId: string) => api.deleteImportBatch(batchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PENDING_KEY });
    },
  });
}
