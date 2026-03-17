import { useQuery } from "@tanstack/react-query";
import { fetchAiAnalysis } from "../services/api";
import type { AiAnalysisResponse } from "../types";
import { useAuth } from "./useAuth";

export function useAiAnalysis() {
  const { user } = useAuth();

  const query = useQuery<AiAnalysisResponse>({
    queryKey: ["ai-analysis", user?.id],
    queryFn: fetchAiAnalysis,
    enabled: !!user,
    staleTime: 10 * 60 * 1000, // 10 min — analise e mensal, cache agressivo
  });

  return {
    analysis: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}
