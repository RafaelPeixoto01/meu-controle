import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useMonthlyView } from "../hooks/useMonthTransition";
import MonthNavigator from "../components/MonthNavigator";
import IncomeTable from "../components/IncomeTable";
import ExpenseTable from "../components/ExpenseTable";
import SaldoLivre from "../components/SaldoLivre";
import ViewSelector from "../components/ViewSelector";
import AlertBanner from "../components/alerts/AlertBanner";
import { useAlerts } from "../hooks/useAlerts";
import { updateExpense } from "../services/api";
import type { Alerta } from "../types";

export default function MonthlyView() {
  const {
    year,
    month,
    data,
    isLoading,
    isError,
    error,
    goToPreviousMonth,
    goToNextMonth,
  } = useMonthlyView();

  const { alertsForTab, dismiss } = useAlerts();
  const queryClient = useQueryClient();

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-6 pb-12 space-y-6">
        <ViewSelector />
        <div className="flex flex-col justify-center items-center py-24 gap-3">
          <div className="h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
          <p className="text-text-muted text-sm font-medium">Carregando dados...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-6 pb-12 space-y-6">
        <ViewSelector />
        <div className="flex flex-col justify-center items-center py-24 gap-2">
          <p className="text-danger font-bold text-lg">
            Erro ao carregar dados
          </p>
          <p className="text-text-muted text-sm">
            {error?.message || "Verifique sua conexão e tente novamente."}
          </p>
        </div>
      </div>
    );
  }
  const tabAlerts = alertsForTab("gastos_planejados");

  const handleAlertAction = useCallback(async (alerta: Alerta) => {
    if (alerta.acao?.tipo === "marcar_pago" && alerta.acao.referencia_id) {
      await updateExpense(alerta.acao.referencia_id, { status: "Pago" });
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      queryClient.invalidateQueries({ queryKey: ["monthly-summary"] });
    }
  }, [queryClient]);

  if (!data) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 pb-12 space-y-6">
      <ViewSelector />
      <AlertBanner alertas={tabAlerts} onDismiss={dismiss} onAction={handleAlertAction} />
      <MonthNavigator
        year={year}
        month={month}
        onPrevious={goToPreviousMonth}
        onNext={goToNextMonth}
      />
      <IncomeTable
        incomes={data.incomes}
        totalReceitas={data.total_receitas}
        year={year}
        month={month}
      />
      <ExpenseTable
        expenses={data.expenses}
        totalDespesas={data.total_despesas}
        totalPago={data.total_pago}
        totalPendente={data.total_pendente}
        totalAtrasado={data.total_atrasado}
        year={year}
        month={month}
      />
      <SaldoLivre
        totalReceitas={data.total_receitas}
        totalDespesas={data.total_despesas}
        saldoLivre={data.saldo_livre}
      />
    </div>
  );
}
