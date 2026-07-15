import { QueryClient } from "@tanstack/react-query";

// CR-041: modulo proprio — quando exportado pelo main.tsx, o entry point
// virava dependencia de outros modulos (AuthContext), causando dupla
// avaliacao do main e o erro "createRoot() on a container that has already
// been passed to createRoot()" em todo load do dev server
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutos
      retry: 1,
    },
  },
});
