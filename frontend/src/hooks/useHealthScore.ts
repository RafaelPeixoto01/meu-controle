import { useQuery } from "@tanstack/react-query";
import { fetchHealthScore, fetchScoreHistory } from "../services/api";
import type { HealthScoreData, ScoreHistoryData } from "../types";
import { useAuth } from "./useAuth";

export function useHealthScore() {
  const { user } = useAuth();

  const scoreQuery = useQuery<HealthScoreData>({
    queryKey: ["health-score", user?.id],
    queryFn: fetchHealthScore,
    enabled: !!user,
  });

  const historyQuery = useQuery<ScoreHistoryData>({
    queryKey: ["score-history", user?.id],
    queryFn: () => fetchScoreHistory(12),
    enabled: !!user,
  });

  return {
    score: scoreQuery.data,
    history: historyQuery.data,
    isLoading: scoreQuery.isLoading || historyQuery.isLoading,
    isError: scoreQuery.isError || historyQuery.isError,
    error: scoreQuery.error || historyQuery.error,
  };
}
