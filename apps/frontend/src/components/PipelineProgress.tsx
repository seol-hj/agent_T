'use client';

import { usePipelineProgress } from '@/hooks/usePipeline';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle2, Loader2, Clock, XCircle, AlertCircle } from 'lucide-react';
import { msToSeconds } from '@/lib/utils';
import type { PipelineStepStatus } from '@/types';

interface PipelineProgressProps {
  executionId: string;
}

export function PipelineProgress({ executionId }: PipelineProgressProps) {
  const { data, isLoading, error } = usePipelineProgress(executionId);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          <span className="ml-2 text-muted-foreground">로딩 중...</span>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive flex items-center">
            <AlertCircle className="mr-2 h-5 w-5" />
            진행률 조회 실패
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {error.message}
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            백엔드에 진행률 조회 API가 구현되지 않았을 수 있습니다.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="py-8">
          <p className="text-center text-muted-foreground">데이터 없음</p>
        </CardContent>
      </Card>
    );
  }

  const getStatusIcon = (status: PipelineStepStatus['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'running':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'pending':
        return <Clock className="h-5 w-5 text-gray-400" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: PipelineStepStatus['status']) => {
    switch (status) {
      case 'completed':
        return '완료';
      case 'running':
        return '진행 중';
      case 'failed':
        return '실패';
      case 'pending':
        return '대기 중';
      case 'skipped':
        return '건너뜀';
      default:
        return status;
    }
  };

  const totalSteps = data.steps.length;
  const completedSteps = data.steps.filter(s => s.status === 'completed').length;
  const progressPercent = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>파이프라인 진행 상황</CardTitle>
          <div className="text-sm text-muted-foreground">
            {completedSteps} / {totalSteps} 단계 ({progressPercent}%)
          </div>
        </div>
        {data.total_duration_ms && (
          <p className="text-sm text-muted-foreground">
            총 소요 시간: {msToSeconds(data.total_duration_ms)}초
          </p>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.steps.map((step, index) => (
            <div key={index} className="flex items-start gap-3 p-3 rounded-lg border bg-card">
              <div className="mt-0.5">{getStatusIcon(step.status)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-medium text-sm truncate">
                    {index + 1}. {step.step_name}
                  </h4>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      step.status === 'completed' ? 'bg-green-100 text-green-700' :
                      step.status === 'running' ? 'bg-blue-100 text-blue-700' :
                      step.status === 'failed' ? 'bg-red-100 text-red-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {getStatusText(step.status)}
                    </span>
                    {step.duration_ms && (
                      <span className="text-xs text-muted-foreground">
                        {msToSeconds(step.duration_ms)}초
                      </span>
                    )}
                  </div>
                </div>
                
                {step.artifact_uri && (
                  <p className="text-xs text-muted-foreground mt-1 truncate">
                    📄 {step.artifact_uri}
                  </p>
                )}
                
                {step.error_message && (
                  <p className="text-xs text-red-500 mt-1">
                    ❌ {step.error_message}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* 전체 상태 표시 */}
        <div className="mt-6 p-4 rounded-lg border bg-muted/50">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">전체 상태</span>
            <span className={`text-sm font-semibold ${
              data.status === 'completed' ? 'text-green-600' :
              data.status === 'failed' ? 'text-red-600' :
              'text-blue-600'
            }`}>
              {data.status === 'completed' ? '완료' :
               data.status === 'failed' ? '실패' : '진행 중'}
            </span>
          </div>
          
          {data.error_message && (
            <p className="text-sm text-red-500 mt-2">
              {data.error_message}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
