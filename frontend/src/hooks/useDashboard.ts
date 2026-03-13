import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchDashboard } from "../services/api";
import {
  getCurrentMonthRef,
  getNextMonth,
  getPreviousMonth,
} from "../utils/date";
import type { DashboardData } from "../types";
import { useAuth } from "./useAuth";

export function useDashboard() {
  const { user } = useAuth();
  const [monthRef, setMonthRef] = useState(getCurrentMonthRef);

  const query = useQuery<DashboardData>({
    queryKey: ["dashboard", user?.id, monthRef.year, monthRef.month],
    queryFn: () => fetchDashboard(monthRef.year, monthRef.month),
    enabled: !!user,
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
