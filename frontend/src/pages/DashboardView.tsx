import { useState, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import ViewSelector from "../components/ViewSelector";
import MonthNavigator from "../components/MonthNavigator";
import KeyIndicators from "../components/dashboard/KeyIndicators";
import CategoryDonutChart from "../components/dashboard/CategoryDonutChart";
import EvolutionBarChart from "../components/dashboard/EvolutionBarChart";
import StatusBreakdown from "../components/dashboard/StatusBreakdown";
import AlertsCard from "../components/alerts/AlertsCard";
import AlertsModal from "../components/alerts/AlertsModal";
import AlertsSettings from "../components/alerts/AlertsSettings";
import { useDashboard } from "../hooks/useDashboard";
import { useAlerts, useAlertsConfig } from "../hooks/useAlerts";
import { updateExpense } from "../services/api";
import type { Alerta } from "../types";

export default function DashboardView() {
  const {
    year,
    month,
    data,
    isLoading,
    isError,
    error,
    goToPreviousMonth,
    goToNextMonth,
  } = useDashboard();

  const { alerts, resumo, dismiss } = useAlerts();
  const { config, updateConfig, isUpdating } = useAlertsConfig();
  const [showAllAlerts, setShowAllAlerts] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const queryClient = useQueryClient();

  const handleAlertAction = useCallback(async (alerta: Alerta) => {
    if (alerta.acao?.tipo === "marcar_pago" && alerta.acao.referencia_id) {
      await updateExpense(alerta.acao.referencia_id, { status: "Pago" });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["monthly-summary"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    }
  }, [queryClient]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 pb-12 space-y-6">
      <ViewSelector />

      <MonthNavigator
        year={year}
        month={month}
        onPrevious={goToPreviousMonth}
        onNext={goToNextMonth}
      />

      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4" />
          <p className="text-text-muted text-sm">Carregando dashboard...</p>
        </div>
      )}

      {isError && (
        <div className="text-center py-12">
          <p className="text-danger font-medium">
            {error?.message || "Erro ao carregar dashboard"}
          </p>
          <p className="text-text-muted text-sm mt-1">
            Verifique sua conexão e tente novamente.
          </p>
        </div>
      )}

      {data && (
        <div className="space-y-6 animate-fade-in-up">
          {/* Alertas Card */}
          <AlertsCard
            alertas={alerts}
            resumo={resumo}
            onDismiss={dismiss}
            onAction={handleAlertAction}
            onViewAll={() => setShowAllAlerts(true)}
            onSettings={() => setShowSettings(true)}
          />

          {/* KPI Cards */}
          <KeyIndicators
            saldoLivre={data.saldo_livre}
            percentualComprometimento={data.percentual_comprometimento}
            totalDespesasPlanejadas={data.total_despesas_planejadas}
            totalGastosDiarios={data.total_gastos_diarios}
          />

          {/* Donut Charts — side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            <CategoryDonutChart
              title="Despesas Planejadas por Categoria"
              data={data.categorias_planejadas}
              total={data.total_despesas_planejadas}
            />
            <CategoryDonutChart
              title="Gastos Diários por Categoria"
              data={data.categorias_diarios}
              total={data.total_gastos_diarios}
            />
          </div>

          {/* Bar Chart — full width */}
          <EvolutionBarChart data={data.evolucao} />

          {/* Status Breakdown */}
          <StatusBreakdown
            totalPago={data.total_pago}
            totalPendente={data.total_pendente}
            totalAtrasado={data.total_atrasado}
          />
        </div>
      )}

      {/* Modais de alertas */}
      {showAllAlerts && (
        <AlertsModal
          alertas={alerts}
          onClose={() => setShowAllAlerts(false)}
          onDismiss={dismiss}
          onAction={handleAlertAction}
        />
      )}
      {showSettings && config && (
        <AlertsSettings
          config={config}
          onClose={() => setShowSettings(false)}
          onSave={(data) => {
            updateConfig(data);
            setShowSettings(false);
          }}
          isSaving={isUpdating}
        />
      )}
    </div>
  );
}
