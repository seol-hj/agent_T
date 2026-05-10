import { QueryClient } from '@tanstack/react-query';

/**
 * React Query Client 설정
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5분
    },
    mutations: {
      retry: 0,
    },
  },
});
