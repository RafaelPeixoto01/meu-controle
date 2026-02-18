import { useState } from "react";
import { useDailyExpensesMonthly } from "./useDailyExpenses";
import {
  getCurrentMonthRef,
  getNextMonth,
  getPreviousMonth,
} from "../utils/date";

export function useDailyExpensesView() {
  const [monthRef, setMonthRef] = useState(getCurrentMonthRef);

  const query = useDailyExpensesMonthly(monthRef.year, monthRef.month);

  function goToPreviousMonth() {
    setMonthRef((prev) => getPreviousMonth(prev.year, prev.month));
  }

  function goToNextMonth() {
    setMonthRef((prev) => getNextMonth(prev.year, prev.month));
  }

  return {
    year: monthRef.year,
    month: monthRef.month,
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    goToPreviousMonth,
    goToNextMonth,
  };
}
