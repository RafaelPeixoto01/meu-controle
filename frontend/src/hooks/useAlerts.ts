import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchAlerts, markAlertSeen, dismissAlert, fetchAlertsConfig, updateAlertsConfig } from "../services/api";
import type { AlertasResponse, Alerta, ConfiguracaoAlertas } from "../types";
import { useAuth } from "./useAuth";

export function useAlerts() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery<AlertasResponse>({
    queryKey: ["alerts", user?.id],
    queryFn: fetchAlerts,
    enabled: !!user,
    staleTime: 30 * 1000, // 30s — alertas mudam com frequência
  });

  const seenMutation = useMutation({
    mutationFn: markAlertSeen,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  const dismissMutation = useMutation({
    mutationFn: dismissAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  function alertsForTab(tab: string): Alerta[] {
    if (!query.data) return [];
    return query.data.alertas.filter(
      (a) => a.contexto_aba === tab && a.status === "ativo"
    );
  }

  return {
    alerts: query.data?.alertas ?? [],
    resumo: query.data?.resumo ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    markSeen: seenMutation.mutate,
    dismiss: dismissMutation.mutate,
    alertsForTab,
  };
}

export function useAlertsConfig() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery<ConfiguracaoAlertas>({
    queryKey: ["alerts-config", user?.id],
    queryFn: fetchAlertsConfig,
    enabled: !!user,
  });

  const mutation = useMutation({
    mutationFn: updateAlertsConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts-config"] });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
  });

  return {
    config: query.data,
    isLoading: query.isLoading,
    updateConfig: mutation.mutate,
    isUpdating: mutation.isPending,
  };
}
