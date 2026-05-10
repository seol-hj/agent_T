'use client';

import { useEffect } from 'react';
import { PipelineProgress } from '@/components/PipelineProgress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { usePipelineProgress } from '@/hooks/usePipeline';
import { ArrowLeft, RefreshCw } from 'lucide-react';

export default function ExperimentRunningPage({ 
  params 
}: { 
  params: { id: string } 
}) {
  const router = useRouter();
  const { data, refetch } = usePipelineProgress(params.id);

  // 완료되면 결과 페이지로 자동 이동
  useEffect(() => {
    if (data?.status === 'completed') {
      // 1초 후 이동 (사용자가 완료 상태를 볼 수 있도록)
      setTimeout(() => {
        router.push(`/experiments/${params.id}/results`);
      }, 1000);
    }
  }, [data?.status, params.id, router]);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/')}
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              대시보드
            </Button>
          </div>
          <h2 className="text-3xl font-bold tracking-tight">실험 실행 중</h2>
          <p className="text-muted-foreground mt-1">
            Execution ID: <code className="text-xs bg-muted px-1 py-0.5 rounded">{params.id}</code>
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
        >
          <RefreshCw className="h-4 w-4 mr-1" />
          새로고침
        </Button>
      </div>

      {/* Progress */}
      <PipelineProgress executionId={params.id} />

      {/* 실패 시 액션 */}
      {data?.status === 'failed' && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">실험 실패</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {data.error_message || '알 수 없는 오류가 발생했습니다.'}
            </p>
            <div className="flex gap-2">
              <Button
                onClick={() => router.push('/experiments/new')}
                variant="outline"
              >
                새 실험 시작
              </Button>
              <Button
                onClick={() => router.push('/')}
                variant="ghost"
              >
                대시보드로 돌아가기
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 완료 메시지 */}
      {data?.status === 'completed' && (
        <Card className="border-green-200 bg-green-50/50">
          <CardContent className="py-6">
            <p className="text-center text-green-700 font-medium">
              ✅ 실험이 성공적으로 완료되었습니다! 결과 페이지로 이동합니다...
            </p>
          </CardContent>
        </Card>
      )}

      {/* Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">실시간 모니터링</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground space-y-2">
          <p>• 진행률은 2초마다 자동으로 업데이트됩니다</p>
          <p>• 완료 시 자동으로 결과 페이지로 이동합니다</p>
          <p>• 페이지를 닫아도 백그라운드에서 계속 실행됩니다</p>
        </CardContent>
      </Card>
    </div>
  );
}
