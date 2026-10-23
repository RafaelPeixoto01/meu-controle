import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createIntegrationToken,
  fetchIntegrationTokens,
  revokeIntegrationToken,
} from "../services/api";
import type { IntegrationToken } from "../types";
import { useAuth } from "./useAuth";

/** CR-058: tokens de integracao do Lumi (Perfil). */
export function useIntegrationTokens() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const query = useQuery<IntegrationToken[]>({
    queryKey: ["integration-tokens", user?.id],
    queryFn: fetchIntegrationTokens,
    enabled: !!user,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["integration-tokens"] });

  const createMutation = useMutation({
    mutationFn: createIntegrationToken,
    onSuccess: invalidate,
  });

  const revokeMutation = useMutation({
    mutationFn: revokeIntegrationToken,
    onSuccess: invalidate,
  });

  return {
    tokens: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    create: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    revoke: revokeMutation.mutateAsync,
    isRevoking: revokeMutation.isPending,
  };
}
