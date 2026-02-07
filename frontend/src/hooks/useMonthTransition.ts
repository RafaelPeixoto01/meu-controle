import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchMonthlySummary } from "../services/api";
import {
  getCurrentMonthRef,
  getNextMonth,
  getPreviousMonth,
} from "../utils/date";
import type { MonthlySummary } from "../types";

export function useMonthlyView() {
  const [monthRef, setMonthRef] = useState(getCurrentMonthRef);

  const query = useQuery<MonthlySummary>({
    queryKey: ["monthly-summary", monthRef.year, monthRef.month],
    queryFn: () => fetchMonthlySummary(monthRef.year, monthRef.month),
  });

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
