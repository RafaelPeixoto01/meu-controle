import { useMonthlyView } from "../hooks/useMonthTransition";
import MonthNavigator from "../components/MonthNavigator";
import IncomeTable from "../components/IncomeTable";
import ExpenseTable from "../components/ExpenseTable";
import SaldoLivre from "../components/SaldoLivre";

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

  if (isLoading) {
    return (
      <div className="flex flex-col justify-center items-center py-24 gap-3">
        <div className="h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p className="text-text-muted text-sm font-medium">Carregando dados...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col justify-center items-center py-24 gap-2">
        <p className="text-danger font-bold text-lg">
          Erro ao carregar dados
        </p>
        <p className="text-text-muted text-sm">
          {error?.message || "Verifique sua conexao e tente novamente."}
        </p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 pb-12 space-y-6">
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
