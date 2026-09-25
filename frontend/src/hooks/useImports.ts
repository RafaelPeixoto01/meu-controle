// CR-047 (F07): hooks TanStack Query da importacao de extratos/faturas.
import { keepPreviousData, useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import * as api from "../services/api";
import type {
  Expense,
  ImportBatch,
  ImportBatchSummary,
  ImportConfirmRequest,
  ImportHistoryPage,
  ImportUndoPreview,
} from "../types";
import { useAuth } from "./useAuth";
import { monthsToFetchForMatches } from "../utils/importReview";

const PENDING_KEY = ["imports-pending"];
// CR-056: todo evento que muda o status de um lote invalida o historico
const HISTORY_KEY = ["imports-history"];
export const HISTORY_PAGE_SIZE = 10;

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
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      // Sem leitura ainda (primeira busca falhou): continuar tentando. Parar
      // aqui deixaria o usuario preso no spinner para sempre, ja que o retry
      // global e 1 e o refetch por foco esta desligado; o erro da tentativa
      // aparece na tela enquanto isso.
      if (!status) return POLL_INTERVAL_MS;
      return status === "processando" ? POLL_INTERVAL_MS : false;
    },
  });
}

export function useUploadImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.uploadImport(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PENDING_KEY });
      queryClient.invalidateQueries({ queryKey: HISTORY_KEY });
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
      queryClient.invalidateQueries({ queryKey: HISTORY_KEY });
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
      queryClient.invalidateQueries({ queryKey: HISTORY_KEY });
    },
  });
}

// ========== CR-056: historico e desfazer ==========

export function useImportHistory(page: number) {
  const { user } = useAuth();
  return useQuery<ImportHistoryPage>({
    queryKey: [...HISTORY_KEY, user?.id, page],
    queryFn: () => api.fetchImportHistory(page, HISTORY_PAGE_SIZE),
    enabled: !!user,
    // Trocar de pagina mantem a anterior na tela ate a nova chegar
    placeholderData: keepPreviousData,
  });
}

export function useUndoPreview(batchId: string | null) {
  const { user } = useAuth();
  return useQuery<ImportUndoPreview>({
    queryKey: ["import-undo-preview", user?.id, batchId],
    queryFn: () => api.fetchUndoPreview(batchId!),
    enabled: !!user && !!batchId,
    // A previa descreve o estado de AGORA: reabrir o dialogo depois de editar
    // um lancamento nao pode mostrar o plano antigo do cache
    staleTime: 0,
    gcTime: 0,
    refetchOnWindowFocus: false,
  });
}

export function useUndoImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (batchId: string) => api.undoImport(batchId),
    onSuccess: () => {
      // O undo apaga gastos e series de parcelas e restaura planejados: alem do
      // que o confirm invalida, a projecao e o score mudam com a serie removida
      queryClient.invalidateQueries({ queryKey: HISTORY_KEY });
      queryClient.invalidateQueries({ queryKey: PENDING_KEY });
      queryClient.invalidateQueries({ queryKey: ["daily-expenses-summary"] });
      queryClient.invalidateQueries({ queryKey: ["monthly-summary"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["installments"] });
      queryClient.invalidateQueries({ queryKey: ["installment-projection"] });
      queryClient.invalidateQueries({ queryKey: ["health-score"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });
}
