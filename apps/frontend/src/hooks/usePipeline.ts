import { useMutation, useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import type { PipelineExecutionRequest } from '@/types';

/**
 * Pipeline 실행 Hook
 */
export function useRunPipeline() {
  const router = useRouter();

  return useMutation({
    mutationFn: (request: PipelineExecutionRequest) => 
      apiClient.runPipeline(request),
    onSuccess: (data) => {
      // 실행 성공 시 모니터링 페이지로 이동
      router.push(`/experiments/${data.execution_id}/running`);
    },
  });
}

/**
 * Pipeline 진행률 조회 Hook
 * 2초마다 폴링하여 실시간 업데이트
 */
export function usePipelineProgress(executionId: string | null) {
  return useQuery({
    queryKey: ['pipeline-progress', executionId],
    queryFn: () => apiClient.getPipelineProgress(executionId!),
    enabled: !!executionId,
    refetchInterval: (query) => {
      // 완료되면 폴링 중지
      const data = query.state.data;
      if (!data) return false;

      const isRunning = data.status !== 'completed' && data.status !== 'failed';
      const hasRunningSteps = data.steps.some(s => s.status === 'running');

      return (isRunning || hasRunningSteps) ? 2000 : false;
    },
  });
}

/**
 * Health Check Hook
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.healthCheck(),
    refetchInterval: 30000, // 30초마다
  });
}
