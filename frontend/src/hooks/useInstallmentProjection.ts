import { useQuery } from "@tanstack/react-query";
import { fetchInstallmentProjection } from "../services/api";
import type { InstallmentProjectionResponse } from "../types";
import { useAuth } from "./useAuth";

export function useInstallmentProjection(months = 12) {
  const { user } = useAuth();

  const query = useQuery<InstallmentProjectionResponse>({
    queryKey: ["installment-projection", user?.id, months],
    queryFn: () => fetchInstallmentProjection(months),
    enabled: !!user,
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
  };
}
