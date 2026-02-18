import { useDailyExpensesView } from "../hooks/useDailyExpensesView";
import MonthNavigator from "../components/MonthNavigator";
import DailyExpenseTable from "../components/DailyExpenseTable";
import ViewSelector from "../components/ViewSelector";

export default function DailyExpensesView() {
  const {
    year,
    month,
    data,
    isLoading,
    isError,
    error,
    goToPreviousMonth,
    goToNextMonth,
  } = useDailyExpensesView();

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-6 pb-12 space-y-6">
        <ViewSelector />
        <div className="flex flex-col justify-center items-center py-24 gap-3">
          <div className="h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
          <p className="text-text-muted text-sm font-medium">
            Carregando dados...
          </p>
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
            {error?.message || "Verifique sua conexao e tente novamente."}
          </p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 pb-12 space-y-6">
      <ViewSelector />
      <MonthNavigator
        year={year}
        month={month}
        onPrevious={goToPreviousMonth}
        onNext={goToNextMonth}
      />
      <DailyExpenseTable
        dias={data.dias}
        totalMes={data.total_mes}
        year={year}
        month={month}
      />
    </div>
  );
}
